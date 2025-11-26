"""
广告追踪 LLM 高价值信息识别作业

功能：
1. 从聊天记录表获取当日 0 点到当前的所有包含图片的聊天记录
2. 提交给 LLM 进行内容分析和风险判别
3. 将判断出具有高价值的信息写入 ad_tracking_high_value_message 表

使用方式：
- 实时处理：处理当日的包含图片的聊天记录
- 手动调用：python -m jd.jobs.ad_tracking_llm

使用示例：
    from jd.jobs.ad_tracking_llm import AdTrackingLLMJob

    job = AdTrackingLLMJob()
    job.process_daily_high_value_messages()
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import logging
import json
from difflib import SequenceMatcher
import requests
import time

from jd import app, db
from jd.models.tg_group_chat_history import TgGroupChatHistory
from jd.models.tg_group import TgGroup
from jd.models.tg_group_user_info import TgGroupUserInfo
from jd.models.ad_tracking_high_value_message import AdTrackingHighValueMessage
from jd.utils.logging_config import get_logger, PerformanceLogger
from config import LLM_CONFIG

logger = get_logger(__name__, {
    'component': 'ad_tracking',
    'module': 'llm_job'
})


class LLMConfig:
    """LLM API 配置 - 智谱清言大模型

    配置源：config.py 中的 LLM_CONFIG
    支持通过环境变量 LLM_API_KEY 覆盖 API KEY
    """

    # LLM API 相关配置（从 config.py 读取）
    LLM_API_ENDPOINT = LLM_CONFIG.get('api_endpoint')
    LLM_API_KEY = LLM_CONFIG.get('api_key')
    LLM_MODEL_TEXT = LLM_CONFIG.get('model_text')
    LLM_MODEL_VISION = LLM_CONFIG.get('model_vision')
    LLM_TIMEOUT = LLM_CONFIG.get('timeout', 30)

    # 限流配置（从 config.py 读取）
    RATE_LIMIT_INTERVAL_SECONDS = LLM_CONFIG.get('rate_limit_interval_seconds', 5)
    RATE_LIMIT_PER_HOUR = LLM_CONFIG.get('rate_limit_per_hour', 10)

    # 提示词相关配置
    SYSTEM_PROMPT = "你是一个打击走私、诈骗、毒品等交易的警员，请识别此聊天记录是否包含可疑的黑灰产交易信息？如果包含，请分析其重要程度（0-100分）和优先级（高/中/低）。"
    USER_PROMPT_TEMPLATE = "群组: {group_name}\n用户: {username}\n内容: {content}"

    @classmethod
    def is_configured(cls) -> bool:
        """检查 LLM 配置是否完整"""
        return all([
            cls.LLM_API_ENDPOINT,
            cls.LLM_API_KEY,
            cls.LLM_MODEL_TEXT or cls.LLM_MODEL_VISION,
        ])


class LLMRateLimiter:
    """LLM 请求限流器

    限制条件：
    1. 请求间隔：每个请求之间必须间隔 5 秒
    2. 小时限制：每小时最多 10 次请求
    """

    def __init__(self, interval_seconds: int = 5, per_hour: int = 10):
        """
        初始化限流器

        Args:
            interval_seconds: 请求间隔（秒）
            per_hour: 每小时最大请求次数
        """
        self.interval_seconds = interval_seconds
        self.per_hour = per_hour
        self.last_request_time = None
        self.hourly_requests = []  # 存储一小时内的请求时间

    def _cleanup_old_requests(self):
        """清理超过一小时的请求记录"""
        now = time.time()
        self.hourly_requests = [
            req_time for req_time in self.hourly_requests
            if now - req_time < 3600
        ]

    def can_request(self) -> Tuple[bool, str]:
        """
        检查是否可以发起请求

        Returns:
            (是否可以请求, 等待理由或提示信息)
        """
        now = time.time()
        self._cleanup_old_requests()

        # 检查小时限制
        if len(self.hourly_requests) >= self.per_hour:
            wait_time = self.hourly_requests[0] + 3600 - now
            return False, f"小时请求限制已达到 ({self.per_hour}次)，还需等待 {wait_time:.1f} 秒"

        # 检查间隔限制
        if self.last_request_time is not None:
            time_since_last = now - self.last_request_time
            if time_since_last < self.interval_seconds:
                wait_time = self.interval_seconds - time_since_last
                return False, f"请求间隔不足，还需等待 {wait_time:.2f} 秒"

        return True, "可以请求"

    def wait_if_needed(self):
        """如果需要，等待直到可以请求"""
        while True:
            can_req, reason = self.can_request()
            if can_req:
                break

            # 提取等待时间
            wait_time = 0.1  # 默认等待时间
            if "还需等待" in reason:
                try:
                    import re
                    match = re.search(r'(\d+\.?\d*)\s*秒', reason)
                    if match:
                        wait_time = float(match.group(1))
                except:
                    pass

            logger.debug(f"限流等待中: {reason}")
            time.sleep(min(wait_time, 1))  # 最多等待1秒，然后重新检查

    def record_request(self):
        """记录一次成功的请求"""
        now = time.time()
        self.last_request_time = now
        self.hourly_requests.append(now)
        self._cleanup_old_requests()
        logger.debug(f"LLM 请求已记录，当前小时内请求次数: {len(self.hourly_requests)}/{self.per_hour}")

    def get_status(self) -> Dict[str, Any]:
        """获取限流器当前状态"""
        self._cleanup_old_requests()
        return {
            'requests_this_hour': len(self.hourly_requests),
            'max_per_hour': self.per_hour,
            'last_request_time': self.last_request_time,
            'interval_seconds': self.interval_seconds
        }


class AdTrackingLLMJob:
    """广告追踪 LLM 高价值信息识别作业"""

    def __init__(self):
        """初始化作业实例"""
        self.batch_size = 100  # 批处理大小
        self.similarity_threshold = 0.9  # 相似度阈值（90%）
        self.performance_logger = PerformanceLogger()
        self.rate_limiter = LLMRateLimiter(
            interval_seconds=LLMConfig.RATE_LIMIT_INTERVAL_SECONDS,
            per_hour=LLMConfig.RATE_LIMIT_PER_HOUR
        )

    def _get_today_messages_with_images(self) -> List[TgGroupChatHistory]:
        """
        获取当日 0 点到当前的所有包含图片的聊天记录

        Returns:
            包含图片的聊天记录列表
        """
        try:
            # 计算当日起始时间（UTC+8）
            now = datetime.now()
            today_start = datetime(now.year, now.month, now.day, 0, 0, 0)

            logger.info(f"获取聊天记录范围: {today_start} 到 {now}")

            # 查询包含图片的聊天记录
            # 图片路径非空表示该消息包含图片
            query = TgGroupChatHistory.query.filter(
                TgGroupChatHistory.postal_time >= today_start,
                TgGroupChatHistory.postal_time <= now,
                TgGroupChatHistory.photo_path != '',
                TgGroupChatHistory.photo_path != None
            )

            messages = query.all()
            logger.info(f"获取包含图片的聊天记录: {len(messages)} 条")

            return messages

        except Exception as e:
            logger.error(f"获取聊天记录失败: {e}", exc_info=True)
            return []

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算两段文本的相似度

        Args:
            text1: 第一段文本
            text2: 第二段文本

        Returns:
            相似度（0-1），1表示完全相同，0表示完全不同
        """
        if not text1 or not text2:
            return 0.0

        # 使用 SequenceMatcher 计算相似度
        ratio = SequenceMatcher(None, text1, text2).ratio()
        return ratio

    def _deduplicate_messages_by_user(self, messages: List[TgGroupChatHistory]
                                      ) -> Tuple[List[TgGroupChatHistory], int]:
        """
        按用户分组，去除同一用户中相似度超过阈值的重复消息

        Args:
            messages: 原始聊天记录列表

        Returns:
            (去重后的消息列表, 去重数量)

        说明：
            按 user_id 分组，对同一用户的消息进行相似度比较。
            如果消息相似度超过 90%，则只保留第一条（时间最早的）。
        """
        # 按用户ID分组
        user_messages = {}
        for msg in messages:
            if msg.user_id not in user_messages:
                user_messages[msg.user_id] = []
            user_messages[msg.user_id].append(msg)

        deduped_messages = []
        dedup_count = 0

        # 对每个用户的消息进行去重
        for user_id, user_msgs in user_messages.items():
            if not user_msgs:
                continue

            # 按发布时间排序（保证保留最早的消息）
            user_msgs_sorted = sorted(user_msgs, key=lambda m: m.postal_time)

            # 第一条消息总是保留
            kept_messages = [user_msgs_sorted[0]]
            kept_indices = [0]

            # 与已保留的消息比较
            for i in range(1, len(user_msgs_sorted)):
                current_msg = user_msgs_sorted[i]
                is_duplicate = False

                # 与已保留的所有消息进行相似度比较
                for kept_idx in kept_indices:
                    kept_msg = user_msgs_sorted[kept_idx]
                    similarity = self._calculate_similarity(
                        current_msg.message,
                        kept_msg.message
                    )

                    # 如果相似度超过阈值，则认为是重复消息
                    if similarity >= self.similarity_threshold:
                        logger.debug(
                            f"去重: 用户 {user_id} 的消息相似度 {similarity:.2%}, "
                            f"保留消息ID: {kept_msg.message_id}, "
                            f"去除消息ID: {current_msg.message_id}"
                        )
                        is_duplicate = True
                        dedup_count += 1
                        break

                # 如果不是重复消息，则保留
                if not is_duplicate:
                    kept_messages.append(current_msg)
                    kept_indices.append(i)

            deduped_messages.extend(kept_messages)

        logger.info(f"去重完成: 原始消息 {len(messages)} 条, "
                   f"去重后 {len(deduped_messages)} 条, "
                   f"去除 {dedup_count} 条重复消息")

        return deduped_messages, dedup_count


    def _prepare_message_for_llm(self, message: TgGroupChatHistory) -> Dict[str, Any]:
        """
        为 LLM 分析准备消息数据

        Args:
            message: 聊天记录

        Returns:
            包含消息信息的字典
        """
        try:
            # 解析图片路径为列表
            images = []
            if message.photo_path:
                # 支持多张图片（以逗号分隔）
                images = [img.strip() for img in message.photo_path.split(',') if img.strip()]

            # 获取群组信息
            group = TgGroup.query.filter_by(chat_id=message.chat_id).first()
            group_name = group.title if group else None

            # 获取用户信息
            user = TgGroupUserInfo.query.filter(
                TgGroupUserInfo.user_id == message.user_id,
                TgGroupUserInfo.chat_id == message.chat_id
            ).first()
            username = message.username or user.username if user else message.username

            # 构建消息数据
            message_data = {
                'user_id': message.user_id,
                'username': username,
                'chat_id': message.chat_id,
                'group_name': group_name,
                'content': message.message,
                'images': images,
                'publish_time': message.postal_time.isoformat() if message.postal_time else None,
                'message_id': message.message_id
            }

            return message_data

        except Exception as e:
            logger.error(f"准备消息数据失败: {e}", exc_info=True)
            return {}

    def _call_llm_for_judgment(self, messages_batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        调用 LLM API 进行高价值信息判别

        Args:
            messages_batch: 消息数据列表（批处理）

        Returns:
            LLM 判别结果列表
        """
        if not LLMConfig.is_configured():
            logger.warning("LLM 配置不完整，无法调用 LLM API")
            return [{}] * len(messages_batch)

        results = []
        for message in messages_batch:
            try:
                # 判断是否有图片，选择相应的模型和提示词
                has_images = message.get('images') and len(message['images']) > 0

                if has_images:
                    # 使用视觉模型处理图片
                    judgment = self._call_llm_with_vision(message)
                else:
                    # 使用文本模型处理文本
                    judgment = self._call_llm_with_text(message)

                # 确保返回有效的判别结果（至少要有 ai_judgment 字段）
                if judgment and judgment.get('ai_judgment'):
                    results.append(judgment)
                else:
                    results.append({})

            except Exception as e:
                logger.error(f"调用 LLM 处理消息失败 (message_id={message.get('message_id')}): {e}", exc_info=True)
                results.append({})

        return results

    def _call_llm_with_text(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用文本模型调用 LLM

        Args:
            message: 消息数据字典

        Returns:
            解析后的 LLM 判别结果
        """
        try:
            # 应用限流
            self.rate_limiter.wait_if_needed()

            # 构建提示词
            prompt = LLMConfig.USER_PROMPT_TEMPLATE.format(
                group_name=message.get('group_name', '未知'),
                username=message.get('username', '未知'),
                content=message.get('content', '')
            )

            # 构建请求载荷
            payload = {
                "model": LLMConfig.LLM_MODEL_TEXT,
                "messages": [
                    {
                        "role": "system",
                        "content": LLMConfig.SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 1,
                "max_tokens": 65536,
                "stream": False
            }

            headers = {
                "Authorization": f"Bearer {LLMConfig.LLM_API_KEY}",
                "Content-Type": "application/json"
            }

            logger.debug(f"调用 LLM 文本模型，message_id={message.get('message_id')}")

            response = requests.post(
                LLMConfig.LLM_API_ENDPOINT,
                json=payload,
                headers=headers,
                timeout=LLMConfig.LLM_TIMEOUT
            )

            response.raise_for_status()
            result = response.json()

            # 请求成功，记录请求
            self.rate_limiter.record_request()

            return self._parse_llm_response(result)

        except requests.exceptions.RequestException as e:
            logger.error(f"LLM API 请求失败: {e}")
            return {}
        except Exception as e:
            logger.error(f"处理 LLM 文本响应失败: {e}", exc_info=True)
            return {}

    def _call_llm_with_vision(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用视觉模型调用 LLM（处理包含图片的消息）

        Args:
            message: 消息数据字典（包含图片）

        Returns:
            解析后的 LLM 判别结果
        """
        try:
            # 应用限流
            self.rate_limiter.wait_if_needed()

            # 构建内容数组（包含图片和文本）
            content = []

            # 添加图片
            images = message.get('images', [])
            for image_url in images:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": image_url}
                })

            # 添加文本提示
            text_prompt = f"这些是来自 {message.get('group_name', '群组')} 的用户 {message.get('username', '用户')} 的消息和图片。\n\n消息内容: {message.get('content', '')}\n\n请分析这些内容是否涉及黑灰产、诈骗、毒品等非法交易。"
            content.append({
                "type": "text",
                "text": f"{LLMConfig.SYSTEM_PROMPT}\n\n{text_prompt}"
            })

            # 构建请求载荷
            payload = {
                "model": LLMConfig.LLM_MODEL_VISION,
                "messages": [
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                "temperature": 1,
                "max_tokens": 65536,
                "stream": False
            }

            headers = {
                "Authorization": f"Bearer {LLMConfig.LLM_API_KEY}",
                "Content-Type": "application/json"
            }

            logger.debug(f"调用 LLM 视觉模型，message_id={message.get('message_id')}, 图片数={len(images)}")

            response = requests.post(
                LLMConfig.LLM_API_ENDPOINT,
                json=payload,
                headers=headers,
                timeout=LLMConfig.LLM_TIMEOUT
            )

            response.raise_for_status()
            result = response.json()

            # 请求成功，记录请求
            self.rate_limiter.record_request()

            return self._parse_llm_response(result)

        except requests.exceptions.RequestException as e:
            logger.error(f"LLM API 请求失败: {e}")
            return {}
        except Exception as e:
            logger.error(f"处理 LLM 视觉响应失败: {e}", exc_info=True)
            return {}

    def _parse_llm_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析 LLM 返回的响应

        Args:
            response: LLM API 返回的原始响应

        Returns:
            解析后的判别结果字典，包含：
            - ai_judgment: 大模型判断结果 (str)
            - importance_score: 重要程度评分 (float, 0-100)
            - is_high_priority: 是否为高优先级 (bool)
        """
        try:
            # 提取 LLM 的响应内容
            if not response or 'choices' not in response:
                logger.warning(f"LLM 响应格式异常: {response}")
                return {}

            choices = response.get('choices', [])
            if not choices:
                logger.warning("LLM 返回空的 choices")
                return {}

            # 获取第一个 choice 的消息内容
            first_choice = choices[0]
            message = first_choice.get('message', {})
            content = message.get('content', '').strip()

            if not content:
                logger.warning("LLM 返回空的内容")
                return {}

            # 解析 LLM 返回的内容
            ai_judgment = content

            # 尝试从内容中提取重要程度分数和优先级
            importance_score = self._extract_importance_score(content)
            is_high_priority = self._extract_priority(content)

            return {
                'ai_judgment': ai_judgment,
                'importance_score': importance_score,
                'is_high_priority': is_high_priority
            }

        except Exception as e:
            logger.error(f"解析 LLM 响应失败: {e}", exc_info=True)
            return {}

    def _extract_importance_score(self, content: str) -> float:
        """
        从 LLM 响应中提取重要程度分数

        Args:
            content: LLM 返回的内容

        Returns:
            重要程度分数 (0-100)
        """
        try:
            import re
            # 匹配常见的分数格式：数字或百分比
            patterns = [
                r'重要程度[：:]\s*(\d+)',  # 重要程度：数字
                r'重要\s*(?:程度)?[：:]\s*(\d+)',  # 重要程度或重要：数字
                r'评(?:分|级)[：:]\s*(\d+)',  # 评分/评级：数字
                r'(?:风险)?评级[：:]\s*(\d+)',  # 评级：数字
                r'(\d+)\s*[分/％%]',  # 数字分或数字%
            ]

            for pattern in patterns:
                match = re.search(pattern, content)
                if match:
                    score = float(match.group(1))
                    return min(100, max(0, score))  # 限制在 0-100 范围内

            # 检查是否明确表示无风险
            if any(keyword in content for keyword in ['无风险', '正常', '无需处理', '不存在风险', '安全']):
                return 0.0

            # 如果内容包含"包含"、"涉及"等关键词，则给予较高分数
            if any(keyword in content for keyword in ['包含', '涉及', '怀疑', '可能', '风险', '警告', '毒品', '诈骗', '违禁']):
                return 70.0

            return 0.0

        except Exception as e:
            logger.debug(f"提取重要程度分数失败: {e}")
            return 0.0

    def _extract_priority(self, content: str) -> bool:
        """
        从 LLM 响应中提取优先级

        Args:
            content: LLM 返回的内容

        Returns:
            是否为高优先级
        """
        try:
            # 检查是否包含"高优先级"、"高风险"、"需要立即"等关键词
            high_priority_keywords = ['高优先级', '高风险', '立即', '紧急', '严重', '确认', '肯定', '明显']
            low_priority_keywords = ['低优先级', '低风险', '不太可能', '无风险', '正常']

            content_lower = content.lower()

            # 检查低优先级关键词
            if any(keyword in content for keyword in low_priority_keywords):
                return False

            # 检查高优先级关键词
            if any(keyword in content for keyword in high_priority_keywords):
                return True

            # 默认：如果包含任何风险指示就标记为高优先级
            risk_keywords = ['包含', '涉及', '怀疑', '可能', '风险', '警告', '诈骗', '毒品', '走私']
            if any(keyword in content for keyword in risk_keywords):
                return True

            return False

        except Exception as e:
            logger.debug(f"提取优先级失败: {e}")
            return False

    def _save_high_value_message(self, message_data: Dict[str, Any],
                                 llm_judgment: Dict[str, Any],
                                 chat_history_id: int) -> Optional[AdTrackingHighValueMessage]:
        """
        将高价值信息保存到数据库

        Args:
            message_data: 消息数据字典
            llm_judgment: LLM 判别结果
            chat_history_id: 聊天记录ID

        Returns:
            创建的 AdTrackingHighValueMessage 对象或 None
        """
        try:
            # 仅根据 LLM 判别结果保存，LLM 有判别结果才保存
            if not (llm_judgment and llm_judgment.get('ai_judgment')):
                return None

            # 检查是否已存在相同的记录（基于 message_id, user_id, chat_id）
            message_id = message_data.get('message_id')
            user_id = message_data.get('user_id')
            chat_id = message_data.get('chat_id')

            existing = AdTrackingHighValueMessage.query.filter(
                AdTrackingHighValueMessage.content.contains(message_id) if message_id else False,
                AdTrackingHighValueMessage.user_id == user_id,
                AdTrackingHighValueMessage.chat_id == chat_id
            ).first() if message_id else None

            if existing:
                logger.debug(f"高价值信息已存在: {message_id}")
                return existing

            # 创建新的高价值信息记录（使用 chat_history_id）
            high_value_msg = AdTrackingHighValueMessage(
                chat_history_id=chat_history_id,
                user_id=message_data.get('user_id'),
                username=message_data.get('username'),
                chat_id=message_data.get('chat_id'),
                group_name=message_data.get('group_name'),
                content=message_data.get('content'),
                images=message_data.get('images'),
                ai_judgment=llm_judgment.get('ai_judgment', ''),
                publish_time=datetime.fromisoformat(message_data['publish_time'])
                    if message_data.get('publish_time') else None,
                importance_score=llm_judgment.get('importance_score', 0),
                is_high_priority=llm_judgment.get('is_high_priority', False),
                remark=f"自动识别于 {datetime.now().isoformat()} | message_id: {message_id}"
            )

            db.session.add(high_value_msg)

            logger.debug(f"保存高价值信息: message_id={message_id}")

            return high_value_msg

        except Exception as e:
            logger.error(f"保存高价值信息失败: {e}", exc_info=True)
            return None

    def process_daily_high_value_messages(self) -> Dict[str, Any]:
        """
        处理当日包含图片的聊天记录，识别高价值信息

        Returns:
            处理结果字典，包含统计信息

        处理流程：
        1. 获取当日 0 点到当前的所有包含图片的聊天记录
        2. 去除重复消息
        3. 批量提交给 LLM 进行分析
        4. 解析 LLM 结果并保存高价值信息到数据库
        5. 记录统计信息和错误情况
        """
        start_time = datetime.now()
        stats = {
            'total_messages': 0,
            'messages_after_dedup': 0,
            'duplicates_removed': 0,
            'llm_calls': 0,
            'high_value_saved': 0,
            'errors': 0,
            'start_time': start_time.isoformat(),
            'end_time': None,
            'duration_seconds': 0
        }

        try:
            logger.info("=" * 80)
            logger.info("开始处理当日高价值信息识别任务")
            logger.info("=" * 80)

            # 1. 获取当日包含图片的聊天记录
            messages = self._get_today_messages_with_images()
            stats['total_messages'] = len(messages)

            # 2. 去除重复消息（相似度超过90%的同用户消息）
            messages, dedup_count = self._deduplicate_messages_by_user(messages)
            stats['messages_after_dedup'] = len(messages)
            stats['duplicates_removed'] = dedup_count

            if not messages:
                logger.info("未找到当日包含图片的聊天记录")
                stats['end_time'] = datetime.now().isoformat()
                stats['duration_seconds'] = (datetime.now() - start_time).total_seconds()
                return stats

            logger.info(f"开始处理 {len(messages)} 条包含图片的聊天记录（去重后）")

            # 3. 批量处理消息
            for batch_idx in range(0, len(messages), self.batch_size):
                batch = messages[batch_idx:batch_idx + self.batch_size]

                logger.info(f"处理批次 {batch_idx // self.batch_size + 1}, "
                           f"消息数: {len(batch)}")

                # 为 LLM 准备消息数据
                messages_for_llm = []
                chat_msgs_map = {}  # 映射消息ID到聊天记录对象，用于获取chat_history_id

                for chat_msg in batch:
                    msg_data = self._prepare_message_for_llm(chat_msg)
                    if msg_data:
                        messages_for_llm.append(msg_data)
                        chat_msgs_map[msg_data.get('message_id')] = chat_msg

                # 处理所有消息（无论是否有LLM配置）
                if messages_for_llm:
                    # 调用 LLM 进行判别（如果配置了的话）
                    if LLMConfig.is_configured():
                        llm_results = self._call_llm_for_judgment(messages_for_llm)
                        stats['llm_calls'] += 1
                    else:
                        # 未配置LLM时，返回空结果
                        llm_results = [{}] * len(messages_for_llm)

                    # 处理结果并保存高价值信息
                    for idx, msg_data in enumerate(messages_for_llm):
                        llm_judgment = llm_results[idx] if idx < len(llm_results) else {}

                        # 获取对应的聊天记录ID
                        message_id = msg_data.get('message_id')
                        chat_msg = chat_msgs_map.get(message_id)
                        chat_history_id = chat_msg.id if chat_msg else None

                        # 保存高价值信息
                        if chat_history_id:
                            high_value = self._save_high_value_message(msg_data, llm_judgment, chat_history_id)
                            if high_value:
                                stats['high_value_saved'] += 1

                db.session.commit()

            logger.info(f"✓ 处理完成！保存 {stats['high_value_saved']} 条高价值信息")

        except Exception as e:
            logger.error(f"处理过程中出现错误: {e}", exc_info=True)
            stats['errors'] += 1
            db.session.rollback()

        finally:
            end_time = datetime.now()
            stats['end_time'] = end_time.isoformat()
            stats['duration_seconds'] = (end_time - start_time).total_seconds()

            # 添加限流器状态统计
            rate_limiter_status = self.rate_limiter.get_status()
            stats['rate_limiter'] = rate_limiter_status

            logger.info("=" * 80)
            logger.info("处理任务完成")
            logger.info(f"统计信息: {json.dumps(stats, indent=2, ensure_ascii=False)}")
            logger.info("=" * 80)

        return stats


# ==================== 命令行入口 ====================

if __name__ == '__main__':
    """
    命令行使用方式：
    python -m jd.jobs.ad_tracking_llm
    """
    # 初始化 Flask 应用
    app.ready(db_switch=True, web_switch=False, worker_switch=False)

    with app.app_context():
        job = AdTrackingLLMJob()
        result = job.process_daily_high_value_messages()

        # 打印处理结果
        print("\n" + "=" * 80)
        print("处理结果统计")
        print("=" * 80)
        for key, value in result.items():
            if isinstance(value, float):
                print(f"{key:<25}: {value:.2f}")
            else:
                print(f"{key:<25}: {value}")
        print("=" * 80)
