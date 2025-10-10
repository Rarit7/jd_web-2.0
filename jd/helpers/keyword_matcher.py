#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
关键词匹配优化器 - 使用 Aho-Corasick 自动机
用于高效的多模式字符串匹配
"""
import logging
from typing import List, Dict, Tuple, Any
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class AhoCorasickMatcher:
    """
    Aho-Corasick 自动机实现

    时间复杂度：
    - 构建: O(m) - m是所有关键词的总长度
    - 匹配: O(n + z) - n是文本长度，z是匹配数量

    相比简单匹配 O(k*n) - k是关键词数量，提升 k 倍性能
    """

    class TrieNode:
        """Trie树节点"""
        def __init__(self):
            self.children = {}  # 子节点字典
            self.fail = None    # 失败指针
            self.output = []    # 输出（匹配的关键词）

    def __init__(self, case_sensitive: bool = False):
        """
        初始化AC自动机

        Args:
            case_sensitive: 是否区分大小写
        """
        self.root = self.TrieNode()
        self.case_sensitive = case_sensitive
        self._keyword_count = 0

    def add_keyword(self, keyword: str, metadata: Any = None):
        """
        添加关键词到AC自动机

        Args:
            keyword: 关键词字符串
            metadata: 关联的元数据（如tag_id等）
        """
        if not keyword:
            return

        # 统一大小写处理
        search_keyword = keyword if self.case_sensitive else keyword.lower()

        node = self.root
        for char in search_keyword:
            if char not in node.children:
                node.children[char] = self.TrieNode()
            node = node.children[char]

        # 存储匹配信息（原始关键词 + 元数据）
        node.output.append({
            'keyword': keyword,
            'metadata': metadata
        })
        self._keyword_count += 1

    def build(self):
        """
        构建失败指针（KMP的失败函数）
        使用BFS遍历Trie树
        """
        queue = deque()

        # 第一层节点的失败指针指向root
        for child in self.root.children.values():
            child.fail = self.root
            queue.append(child)

        # BFS构建失败指针
        while queue:
            current = queue.popleft()

            for char, child in current.children.items():
                queue.append(child)

                # 寻找失败节点
                fail_node = current.fail
                while fail_node and char not in fail_node.children:
                    fail_node = fail_node.fail

                # 设置失败指针
                child.fail = fail_node.children[char] if fail_node else self.root

                # 合并输出（继承失败节点的输出）
                if child.fail.output:
                    child.output.extend(child.fail.output)

    def search(self, text: str) -> List[Dict[str, Any]]:
        """
        在文本中搜索所有关键词

        Args:
            text: 待搜索的文本

        Returns:
            匹配结果列表，每个元素包含：
            - keyword: 匹配的关键词
            - position: 匹配位置
            - metadata: 关联的元数据
        """
        if not text:
            return []

        # 统一大小写处理
        search_text = text if self.case_sensitive else text.lower()

        matches = []
        node = self.root

        for i, char in enumerate(search_text):
            # 沿着失败指针查找匹配
            while node != self.root and char not in node.children:
                node = node.fail

            # 转移到下一个节点
            if char in node.children:
                node = node.children[char]

            # 输出所有匹配
            if node.output:
                for match in node.output:
                    matches.append({
                        'keyword': match['keyword'],
                        'position': i - len(match['keyword']) + 1,
                        'metadata': match['metadata']
                    })

        return matches

    def search_unique(self, text: str) -> List[Dict[str, Any]]:
        """
        搜索并去重（同一关键词只返回第一次匹配）

        Args:
            text: 待搜索的文本

        Returns:
            去重后的匹配结果列表
        """
        all_matches = self.search(text)

        # 使用字典去重（保留第一次匹配）
        unique_matches = {}
        for match in all_matches:
            keyword = match['keyword']
            if keyword not in unique_matches:
                unique_matches[keyword] = match

        return list(unique_matches.values())

    def get_stats(self) -> Dict[str, int]:
        """获取统计信息"""
        return {
            'keyword_count': self._keyword_count,
            'root_children': len(self.root.children)
        }


class KeywordMatcherCache:
    """
    关键词匹配器缓存管理
    整合AC自动机和缓存机制
    """

    def __init__(self, cache_ttl: int = 300):
        """
        初始化缓存管理器

        Args:
            cache_ttl: 缓存过期时间（秒）
        """
        self.cache_ttl = cache_ttl
        self._matcher = None
        self._cache_timestamp = None
        self._keyword_mappings = None

    def build_matcher(self, keyword_mappings: List[Any]) -> AhoCorasickMatcher:
        """
        从关键词映射构建AC自动机

        Args:
            keyword_mappings: 关键词映射列表（TagKeywordMapping对象）

        Returns:
            构建好的AC自动机
        """
        import datetime

        current_time = datetime.datetime.now()

        # 检查缓存是否有效
        if (self._matcher and self._cache_timestamp and
            (current_time - self._cache_timestamp).total_seconds() < self.cache_ttl and
            self._keyword_mappings == keyword_mappings):
            logger.debug("Using cached AC matcher")
            return self._matcher

        # 构建新的AC自动机
        logger.info(f"Building AC matcher with {len(keyword_mappings)} keywords")
        matcher = AhoCorasickMatcher(case_sensitive=False)

        for mapping in keyword_mappings:
            # 元数据包含tag_id和auto_focus等信息
            metadata = {
                'tag_id': mapping.tag_id,
                'auto_focus': mapping.auto_focus,
                'mapping_id': mapping.id
            }
            matcher.add_keyword(mapping.keyword, metadata)

        # 构建失败指针
        matcher.build()

        # 更新缓存
        self._matcher = matcher
        self._cache_timestamp = current_time
        self._keyword_mappings = keyword_mappings

        stats = matcher.get_stats()
        logger.info(f"AC matcher built: {stats['keyword_count']} keywords, "
                   f"{stats['root_children']} root children")

        return matcher

    def match_keywords(self, text: str, keyword_mappings: List[Any]) -> List[Dict[str, Any]]:
        """
        使用AC自动机匹配关键词

        Args:
            text: 待匹配的文本
            keyword_mappings: 关键词映射列表

        Returns:
            匹配到的关键词信息列表
        """
        if not text or not text.strip():
            return []

        # 构建或获取缓存的matcher
        matcher = self.build_matcher(keyword_mappings)

        # 执行匹配（去重）
        matches = matcher.search_unique(text)

        # 转换为标准格式
        results = []
        for match in matches:
            metadata = match['metadata']
            results.append({
                'tag_id': metadata['tag_id'],
                'keyword': match['keyword'],
                'auto_focus': metadata['auto_focus'],
                'mapping_id': metadata['mapping_id'],
                'position': match['position']
            })

        return results


def benchmark_matchers(text: str, keywords: List[str], iterations: int = 100):
    """
    性能基准测试：对比简单匹配 vs AC自动机

    Args:
        text: 测试文本
        keywords: 关键词列表
        iterations: 迭代次数
    """
    import time

    print(f"\n性能基准测试")
    print(f"文本长度: {len(text)}")
    print(f"关键词数量: {len(keywords)}")
    print(f"迭代次数: {iterations}")
    print("=" * 60)

    # 测试1: 简单in操作
    start = time.time()
    for _ in range(iterations):
        matches = []
        text_lower = text.lower()
        for keyword in keywords:
            if keyword.lower() in text_lower:
                matches.append(keyword)
    simple_time = time.time() - start

    print(f"简单匹配: {simple_time:.4f}秒 ({simple_time/iterations*1000:.2f}ms/次)")

    # 测试2: AC自动机
    matcher = AhoCorasickMatcher(case_sensitive=False)
    for keyword in keywords:
        matcher.add_keyword(keyword, {'keyword': keyword})
    matcher.build()

    start = time.time()
    for _ in range(iterations):
        matches = matcher.search_unique(text)
    ac_time = time.time() - start

    print(f"AC自动机: {ac_time:.4f}秒 ({ac_time/iterations*1000:.2f}ms/次)")
    print(f"性能提升: {simple_time/ac_time:.2f}x")
    print("=" * 60)


if __name__ == "__main__":
    # 示例测试
    text = """
    这是一个测试文本，包含化工产品信息。
    聚乙烯PE供应商，PVC材料批发，化学试剂采购。
    联系方式：WeChat: supplier123
    Chemical supplier for industrial use.
    """

    keywords = [
        "聚乙烯", "PVC", "化学试剂", "供应商", "WeChat",
        "Chemical", "supplier", "PE", "材料", "批发"
    ]

    # 基准测试
    benchmark_matchers(text, keywords * 10, iterations=1000)  # 100个关键词

    # 功能测试
    print("\n功能测试:")
    matcher = AhoCorasickMatcher(case_sensitive=False)
    for kw in keywords:
        matcher.add_keyword(kw, {'name': kw})
    matcher.build()

    matches = matcher.search_unique(text)
    print(f"找到 {len(matches)} 个匹配:")
    for match in matches:
        print(f"  - '{match['keyword']}' at position {match['position']}")
