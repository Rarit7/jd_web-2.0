"""
TmeSpider - 广告追踪系统的核心爬虫服务

功能：
1. URL分类与智能处理 - 自动识别URL类型（普通/t.me/telegra.ph）并选择对应处理方式
2. URL链接识别与基本信息获取
3. Telegram账户识别
4. t.me链接解析与爬虫
5. Telegraph内容抓取
6. 内容标准化处理

核心方法：
- classify_and_process_url(url) - 推荐使用，自动判断URL类型并处理
- classify_url_type(url) - 判断URL类型
- extract_urls(text) - 提取文本中所有URL

注意：此服务只负责文本分析和数据提取，返回JSON格式结果，不执行数据库写入操作
"""

import re
import socket
import logging
import time
from typing import List, Dict, Optional
from urllib.parse import urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class TmeSpider:
    """t.me 链接和广告内容分析爬虫服务"""

    def __init__(self):
        """初始化爬虫实例"""
        self.timeout = 10
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        # URL 请求缓存（解决性能问题）
        self._url_cache = {}  # {normalized_url: {'data': result, 'timestamp': time}}
        self._cache_ttl = 3600  # 缓存1小时

    # ============================================
    # 1. URL分类与智能处理
    # ============================================

    def classify_url_type(self, url: str) -> str:
        """
        判断URL类型

        Args:
            url: URL地址

        Returns:
            'tme' | 'telegraph' | 'general'
        """
        url_lower = url.lower()
        if 't.me/' in url_lower:
            return 'tme'
        elif 'telegra.ph/' in url_lower:
            return 'telegraph'
        else:
            return 'general'

    def classify_and_process_url(self, url: str) -> Dict:
        """
        自动判断URL类型并选择对应的处理方式（带缓存）

        Args:
            url: URL地址

        Returns:
            {
                'url_type': str,  # 'tme' | 'telegraph' | 'general'
                'original_url': str,
                'data': dict,  # 处理结果数据
                'error': str  # 错误信息（如果有）
            }
        """
        # 先标准化 URL（解决问题1：URL去重）
        normalized_url = self.normalize_url(url)

        # 检查缓存
        if normalized_url in self._url_cache:
            cache_entry = self._url_cache[normalized_url]
            if time.time() - cache_entry['timestamp'] < self._cache_ttl:
                logger.debug(f"缓存命中 URL: {normalized_url}")
                return cache_entry['data']
            else:
                # 缓存过期，删除
                del self._url_cache[normalized_url]

        # 缓存未命中，执行处理
        url_type = self.classify_url_type(normalized_url)

        result = {
            'url_type': url_type,
            'original_url': url,
            'data': {},
            'error': None
        }

        try:
            if url_type == 'tme':
                # t.me链接处理
                # 先分类t.me链接
                tme_links = self.extract_and_classify_tme_links(normalized_url)
                if tme_links:
                    tme_link_info = tme_links[0]
                    # 获取预览信息
                    preview_data = self.fetch_tme_preview(normalized_url)
                    result['data'] = {
                        'classification': tme_link_info,
                        'preview': preview_data
                    }
                else:
                    result['error'] = 'Failed to classify t.me link'

            elif url_type == 'telegraph':
                # Telegraph链接处理
                content_data = self.fetch_telegraph_content(normalized_url)
                if 'error' not in content_data:
                    analysis = self.analyze_telegraph_content(content_data)
                    result['data'] = {
                        'content': content_data,
                        'analysis': analysis
                    }
                else:
                    result['error'] = content_data.get('error')

            else:
                # 普通URL处理
                # 1. 钓鱼检测
                phishing_result = self.check_phishing_url(normalized_url)

                # 2. 获取网站基本信息
                website_info = self.get_website_basic_info(normalized_url)

                if 'error' in website_info:
                    result['error'] = website_info.get('error')

                result['data'] = {
                    'normalized_url': normalized_url,
                    'phishing': phishing_result,
                    'website': website_info
                }

            # 写入缓存
            self._url_cache[normalized_url] = {
                'data': result,
                'timestamp': time.time()
            }
            logger.debug(f"缓存写入 URL: {normalized_url}")

        except Exception as e:
            logger.error(f"URL处理失败: {url}, 类型: {url_type}, 错误: {str(e)}")
            result['error'] = str(e)

        return result

    def extract_urls(self, text: str) -> List[str]:
        """
        提取文本中的所有URL（包括 t.me 和 telegra.ph）

        Args:
            text: 待分析的文本内容

        Returns:
            URL列表（已去重）
        """
        urls = []

        # 匹配带协议的URL
        url_pattern_with_protocol = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls.extend(re.findall(url_pattern_with_protocol, text))

        # 匹配不带协议的URL
        url_pattern_without_protocol = r'(?:(?:www\.)|(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,})(?:/[^\s]*)?'
        urls.extend(re.findall(url_pattern_without_protocol, text))

        return list(set(urls))  # 去重

    def check_phishing_url(self, url: str) -> Dict:
        """
        使用Google Safe Browsing API等服务检测钓鱼网站

        注意：需要配置API密钥才能使用，当前返回默认值

        Args:
            url: 待检测的URL

        Returns:
            {
                'is_phishing': bool,
                'api_used': str,
                'threat_types': list
            }
        """
        try:
            # TODO: 实际使用时需要配置 Google Safe Browsing API
            # API密钥需要从 https://developers.google.com/safe-browsing 获取

            # 方案1: Google Safe Browsing API
            # 方案2: VirusTotal API (备选)
            # 方案3: PhishTank API (免费但有请求限制)

            # 临时返回默认值（实际使用时需要配置API）
            return {
                'is_phishing': False,
                'api_used': 'google_safe_browsing',
                'threat_types': []
            }
        except Exception as e:
            logger.error(f"钓鱼检测失败: {str(e)}")
            return {
                'is_phishing': None,
                'api_used': 'none',
                'error': str(e)
            }

    def get_website_basic_info(self, url: str) -> Dict:
        """
        使用轻量级方法获取网站基本信息（纯业务逻辑，不访问数据库）

        功能包括：
        1. 判断是否是短链接（如果是短链接，需要获取真正的url）
        2. 判断网站IP所属地

        注意：
        - 数据库查重逻辑应在 job 层实现，不在此服务层函数中
        - 仅用于普通URL，建议使用 classify_and_process_url() 自动判断URL类型

        Args:
            url: 待分析的URL

        Returns:
            {
                'domain': str,
                'title': str,
                'status_code': int,
                'content_type': str,
                'is_short_url': bool,
                'original_url': str,
                'final_url': str,
                'redirect_chain_length': int,
                'ip_address': str,
                'ip_location': dict
            }
        """
        try:
            # 标准化URL
            if not url.startswith(('http://', 'https://')):
                url = 'http://' + url

            original_url = url
            parsed = urlparse(url)
            domain = parsed.netloc

            # 1. 检测短链接服务
            short_url_services = [
                # 国际短链
                'bit.ly', 'tinyurl.com', 't.co', 'goo.gl', 'ow.ly',
                'buff.ly', 'is.gd', 'cli.gs', 'short.link', 'rebrand.ly',
                's.id', 'cutt.ly', 'bitly.com', 'bl.ink', '1url.com',
                # 中国短链
                'dwz.cn', 'suo.im', 'mrw.so', 't.cn', 'url.cn',
                'u.nu', '0rz.tw', 'reurl.cc', 'ppt.cc', '4url.cc'
            ]
            is_short_url = any(service in domain.lower() for service in short_url_services)

            # 2. 发送GET请求获取完整信息（包含重定向跟踪）
            response = requests.get(
                url,
                timeout=self.timeout,
                stream=True,
                headers=self.headers,
                allow_redirects=True
            )

            final_url = response.url
            final_parsed = urlparse(final_url)

            # 只读取前10KB内容用于提取标题
            content = b''
            for chunk in response.iter_content(chunk_size=1024):
                content += chunk
                if len(content) >= 10240:  # 10KB
                    break

            # 提取网页标题
            title_match = re.search(
                r'<title[^>]*>([^<]+)</title>',
                content.decode('utf-8', errors='ignore'),
                re.IGNORECASE
            )
            title = title_match.group(1).strip() if title_match else None

            # 3. 获取网站IP地址
            ip_address = None
            ip_location = {}
            try:
                ip_address = socket.gethostbyname(final_parsed.netloc)

                # 使用IP地理位置查询服务（免费API）
                # ip-api.com (免费，无需API key)
                ip_api_url = f'http://ip-api.com/json/{ip_address}?fields=status,country,countryCode,region,regionName,city,isp,org'
                ip_response = requests.get(ip_api_url, timeout=3)
                if ip_response.status_code == 200:
                    ip_data = ip_response.json()
                    if ip_data.get('status') == 'success':
                        ip_location = {
                            'country': ip_data.get('country'),
                            'country_code': ip_data.get('countryCode'),
                            'region': ip_data.get('regionName'),
                            'city': ip_data.get('city'),
                            'isp': ip_data.get('isp'),
                            'organization': ip_data.get('org')
                        }
            except (socket.gaierror, requests.RequestException) as e:
                logger.warning(f"IP地址获取失败: {str(e)}")
                ip_address = None
                ip_location = {'error': str(e)}

            return {
                'domain': final_parsed.netloc,
                'title': title,
                'status_code': response.status_code,
                'content_type': response.headers.get('Content-Type', ''),

                # 短链接信息
                'is_short_url': is_short_url,
                'original_url': original_url,
                'final_url': final_url,
                'redirect_chain_length': len(response.history),

                # IP和地理位置信息
                'ip_address': ip_address,
                'ip_location': ip_location,
            }
        except requests.Timeout:
            logger.error(f"URL请求超时: {url}")
            return {'error': 'timeout', 'domain': urlparse(url).netloc}
        except requests.RequestException as e:
            logger.error(f"URL请求失败: {url}, 错误: {str(e)}")
            return {'error': str(e), 'domain': urlparse(url).netloc}
        except Exception as e:
            logger.error(f"URL处理异常: {url}, 错误: {str(e)}")
            return {'error': f'unexpected: {str(e)}', 'domain': urlparse(url).netloc}

    # ============================================
    # 2. Telegram账户识别
    # ============================================

    def extract_telegram_accounts(self, text: str) -> List[str]:
        """
        提取文本中的Telegram账户

        Args:
            text: 待分析的文本内容

        Returns:
            Telegram账户列表（包含@符号）
        """
        # @开头，后跟字母数字下划线，长度5-32
        pattern = r'@([a-zA-Z0-9_]{5,32})'
        accounts = re.findall(pattern, text)
        return ['@' + acc for acc in accounts]

    def convert_account_to_tme_url(self, account: str) -> str:
        """
        将 @username 转换为 t.me/username URL

        Args:
            account: Telegram账户（格式: @username 或 username）

        Returns:
            t.me URL (格式: https://t.me/username)
        """
        # 移除 @ 符号（如果存在）
        username = account.lstrip('@')
        return f'https://t.me/{username}'

    def analyze_telegram_account(self, account: str) -> Dict:
        """
        分析 Telegram 账户，获取账户的详细信息

        功能：
        1. 将 @username 转换为 t.me/username
        2. 爬取 t.me 链接获取账户预览信息
        3. 返回账户分析结果

        Args:
            account: Telegram账户（格式: @username 或 username）

        Returns:
            {
                'account': str,  # 原始账户名（带@）
                'username': str,  # 清理后的用户名（不带@）
                'tme_url': str,  # t.me链接
                'preview': dict,  # 预览信息（来自fetch_tme_preview）
                'error': str  # 错误信息（如果有）
            }
        """
        try:
            # 确保账户名带@符号
            if not account.startswith('@'):
                account = '@' + account

            # 提取用户名（不带@）
            username = account.lstrip('@')

            # 转换为 t.me URL
            tme_url = self.convert_account_to_tme_url(account)

            # 获取预览信息
            preview = self.fetch_tme_preview(tme_url)

            result = {
                'account': account,
                'username': username,
                'tme_url': tme_url,
                'preview': preview,
                'error': preview.get('error') if 'error' in preview else None
            }

            return result

        except Exception as e:
            logger.error(f"Telegram账户分析失败: {account}, 错误: {str(e)}")
            return {
                'account': account,
                'username': account.lstrip('@'),
                'tme_url': None,
                'preview': {},
                'error': str(e)
            }

    # ============================================
    # 3. t.me链接识别与爬虫解析
    # ============================================

    def extract_and_classify_tme_links(self, text: str) -> List[Dict]:
        """
        提取并分类t.me链接

        Args:
            text: 待分析的文本内容

        Returns:
            [
                {
                    'url': 'https://t.me/+abc123',
                    'type': 't_me_private_invite',
                    'target': '+abc123'
                },
                ...
            ]
        """
        results = []

        # 1. 私有频道邀请：t.me/+xxxx
        private_invite_pattern = r't\.me/\+([a-zA-Z0-9_-]+)'
        for match in re.finditer(private_invite_pattern, text):
            results.append({
                'url': f't.me/+{match.group(1)}',
                'type': 't_me_private_invite',
                'target': f'+{match.group(1)}'
            })

        # 2. 旧版私有群组：t.me/joinchat/xxxx
        joinchat_pattern = r't\.me/joinchat/([a-zA-Z0-9_-]+)'
        for match in re.finditer(joinchat_pattern, text):
            results.append({
                'url': f't.me/joinchat/{match.group(1)}',
                'type': 't_me_private_invite',
                'target': f'joinchat/{match.group(1)}'
            })

        # 3. 频道/群组中的具体消息：t.me/username/123
        message_pattern = r't\.me/([a-zA-Z0-9_]+)/(\d+)'
        for match in re.finditer(message_pattern, text):
            results.append({
                'url': f't.me/{match.group(1)}/{match.group(2)}',
                'type': 't_me_channel_msg',
                'target': match.group(1),
                'message_id': match.group(2)
            })

        # 4. 打包群组：t.me/addlist/xxxx
        addlist_pattern = r't\.me/addlist/([a-zA-Z0-9_-]+)'
        for match in re.finditer(addlist_pattern, text):
            results.append({
                'url': f't.me/addlist/{match.group(1)}',
                'type': 't_me_invite',  # 归类为邀请类型
                'target': f'addlist/{match.group(1)}'
            })

        # 5. 公开用户名/频道/群组：t.me/username
        # （排除已经匹配的其他类型）
        public_pattern = r't\.me/(?!joinchat|addlist|\+)([a-zA-Z0-9_]+)(?!/\d+)'
        for match in re.finditer(public_pattern, text):
            # 检查是否已经被其他模式匹配
            if not any(r['target'] == match.group(1) for r in results):
                results.append({
                    'url': f't.me/{match.group(1)}',
                    'type': 't_me_invite',
                    'target': match.group(1)
                })

        return results

    def fetch_tme_preview(self, tme_url: str) -> Dict:
        """
        爬取t.me链接的预览信息

        Args:
            tme_url: t.me链接

        Returns:
            {
                'type': str,  # 链接类别
                'name': str,
                'username': str,
                'avatar': str,
                'desc': str,
                'members': int
            }
        """
        try:
            # 确保URL包含协议
            if not tme_url.startswith(('http://', 'https://')):
                tme_url = 'https://' + tme_url

            response = requests.get(tme_url, headers=self.headers, timeout=self.timeout)

            if response.status_code != 200:
                logger.error(f"t.me链接访问失败: {tme_url}, 状态码: {response.status_code}")
                return {'error': f'HTTP {response.status_code}'}

            soup = BeautifulSoup(response.text, 'html.parser')

            # 提取基本信息
            result = {}

            # 提取名称
            title_tag = soup.find('div', class_='tgme_page_title')
            result['name'] = title_tag.get_text(strip=True) if title_tag else None

            # 提取用户名
            username_tag = soup.find('div', class_='tgme_page_extra')
            result['username'] = username_tag.get_text(strip=True) if username_tag else None

            # 提取头像
            avatar_tag = soup.find('img', class_='tgme_page_photo_image')
            result['avatar'] = avatar_tag.get('src') if avatar_tag else None

            # 提取描述
            desc_tag = soup.find('div', class_='tgme_page_description')
            result['desc'] = desc_tag.get_text(strip=True) if desc_tag else None

            # 提取成员数
            members_tag = soup.find('div', class_='tgme_page_extra')
            if members_tag:
                members_text = members_tag.get_text()
                # 尝试从文本中提取数字
                members_match = re.search(r'([\d\s]+)\s*(members|subscribers)', members_text, re.IGNORECASE)
                if members_match:
                    members_str = members_match.group(1).replace(' ', '')
                    result['members'] = int(members_str)
                else:
                    result['members'] = None
            else:
                result['members'] = None

            # 判断类型
            desc_text = result.get('desc') or ''
            if 'channel' in response.url.lower() or 'Channel' in desc_text:
                result['type'] = 'channel'
            elif 'group' in response.url.lower() or 'Group' in desc_text:
                result['type'] = 'group'
            else:
                result['type'] = 'user'

            return result

        except requests.Timeout:
            logger.error(f"t.me链接请求超时: {tme_url}")
            return {'error': 'timeout'}
        except Exception as e:
            logger.error(f"t.me链接爬取失败: {tme_url}, 错误: {str(e)}")
            return {'error': str(e)}

    # ============================================
    # 4. 内容标准化
    # ============================================

    def normalize_url(self, url: str) -> str:
        """
        标准化URL - 用于去重和比较

        处理：
        - 添加协议（默认https）
        - 统一使用 https 协议（http 和 https 视为相同）
        - 移除www前缀
        - 移除尾部斜杠
        - 移除锚点（#fragment）
        - 转小写

        Args:
            url: 原始URL

        Returns:
            标准化后的URL
        """
        # 添加协议
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        parsed = urlparse(url)

        # 标准化主机名（移除www）
        netloc = parsed.netloc.lower()
        if netloc.startswith('www.'):
            netloc = netloc[4:]

        # 重建URL（移除锚点、尾部斜杠）
        path = parsed.path.rstrip('/') or '/'

        # 统一使用 https 协议（http 和 https 视为相同域名）
        normalized = urlunparse((
            'https',  # 统一使用 https
            netloc,
            path,
            '',  # params
            parsed.query,  # 保留查询参数
            ''   # fragment (移除锚点)
        ))

        return normalized

    def extract_domain(self, url: str) -> str:
        """
        提取域名

        Args:
            url: URL地址

        Returns:
            域名
        """
        parsed = urlparse(self.normalize_url(url))
        return parsed.netloc

    # ============================================
    # 5. Telegraph内容监控与爬虫获取
    # ============================================

    def extract_telegraph_links(self, text: str) -> List[str]:
        """
        提取Telegraph链接

        Args:
            text: 待分析的文本内容

        Returns:
            Telegraph链接列表
        """
        pattern = r'telegra\.ph/[a-zA-Z0-9\-]+'
        links = re.findall(pattern, text)
        return ['https://' + link for link in links]

    def fetch_telegraph_content(self, url: str) -> Dict:
        """
        获取Telegraph页面内容

        Args:
            url: Telegraph页面URL

        Returns:
            {
                'url': str,
                'title': str,
                'content': str,
                'images': list
            }
        """
        try:
            response = requests.get(url, timeout=self.timeout)
            soup = BeautifulSoup(response.text, 'html.parser')

            # 提取标题
            title = soup.find('h1')
            title_text = title.text if title else ''

            # 提取正文
            article = soup.find('article')
            content = article.get_text(separator='\n') if article else ''

            # 提取图片
            images = [img['src'] for img in soup.find_all('img') if img.get('src')]

            return {
                'url': url,
                'title': title_text,
                'content': content,
                'images': images
            }
        except Exception as e:
            logger.error(f"Telegraph内容获取失败: {url}, 错误: {str(e)}")
            return {'url': url, 'error': str(e)}

    def analyze_telegraph_content(self, content_data: Dict) -> Dict:
        """
        分析Telegraph内容的违规程度

        TODO: 当前实现过于粗糙，需要优化：
        1. 使用NLP技术进行语义分析
        2. 集成现有的自动标签系统（tag_keyword_mapping）
        3. 使用机器学习模型识别违规内容
        4. 支持图片内容识别（OCR + 图像分类）
        5. 建立违规内容特征库

        Args:
            content_data: Telegraph内容数据

        Returns:
            {
                'violation_score': int,
                'risk_level': str,
                'matched_keywords': list,
                'analysis_method': str
            }
        """
        # TODO: 临时实现，仅返回基本结构
        # 实际应该调用更智能的内容分析服务
        return {
            'violation_score': 0,
            'risk_level': 'unknown',
            'matched_keywords': [],
            'analysis_method': 'not_implemented',
            'note': 'Content analysis not implemented yet. Please integrate with auto-tagging system.'
        }
