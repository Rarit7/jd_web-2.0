# TgGroupInfoManager 测试文档

## 概述

这个目录包含了 `TgGroupInfoManager` 类的Mock测试，用于验证Telegram群组信息同步功能的正确性。

## 测试文件

- `test_tg_group_info.py` - 主要的测试文件，包含所有mock测试用例

## 测试覆盖范围

### 主要功能测试

1. **sync_all_group_info()** - 同步所有群组信息
   - 成功同步多个群组
   - 处理API异常情况
   - 统计信息正确性

2. **_process_single_group()** - 处理单个群组
   - 处理现有群组
   - 处理新群组
   - 正确调用子方法

3. **_update_existing_group()** - 更新现有群组信息
   - 检测字段变化
   - 记录信息变更
   - 数据库更新操作

4. **_create_new_group()** - 创建新群组
   - 正确创建TgGroup实例
   - 数据库插入操作

5. **_update_group_status()** - 更新群组状态
   - 现有记录更新（有/无成员变化）
   - 新记录创建
   - 消息统计更新

6. **_record_group_info_change()** - 记录信息变更
   - 正确创建变更记录
   - 异常处理和数据库回滚

7. **sync_group_info_by_account()** - 按账户同步
   - TG服务初始化
   - 资源清理
   - 异常处理

### 测试特点

- **完全Mock化** - 不依赖真实数据库或TG API
- **异常处理** - 测试各种错误情况
- **边界条件** - 测试空值、重复数据等情况
- **资源管理** - 验证资源正确创建和释放

## 如何运行测试

### 方法1：使用项目根目录的脚本
```bash
cd /home/ec2-user/workspace/jd_web
python run_tests.py
```

### 方法2：直接运行测试文件
```bash
cd /home/ec2-user/workspace/jd_web/tests
python test_tg_group_info.py
```

### 方法3：使用unittest模块
```bash
cd /home/ec2-user/workspace/jd_web
python -m unittest tests.test_tg_group_info -v
```

## 测试结果解读

测试运行后会显示：
- 运行的测试数量
- 成功/失败/错误的测试数量
- 详细的失败和错误信息

示例输出：
```
测试总结:
运行测试: 12
失败: 0
错误: 0
跳过: 0

✅ 所有测试通过！
```

## 添加新测试

要添加新的测试用例，请在 `TestTgGroupInfoManager` 类中添加以 `test_` 开头的方法：

```python
def test_new_functionality(self):
    """测试新功能"""
    # 准备测试数据
    # 执行测试
    # 验证结果
    pass
```

## 注意事项

1. 所有测试都使用Mock对象，不会访问真实的数据库或TG API
2. 测试环境变量 `TESTING=True` 用于区分测试和生产环境
3. 如需集成测试，请在 `TestTgGroupInfoManagerIntegration` 类中添加
4. Mock测试主要验证业务逻辑，不验证数据库操作的SQL正确性

## 依赖

- `unittest` - Python标准测试框架
- `unittest.mock` - Mock对象支持
- 项目的业务逻辑模块