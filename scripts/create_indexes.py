#!/usr/bin/env python
"""
创建数据库索引以优化getUserStats API性能
"""
import sys
sys.path.insert(0, '/home/ec2-user/workspace/jd_web')

from jd import db, app

def create_indexes():
    """创建优化索引"""
    with app.app_context():
        try:
            # 获取数据库连接
            connection = db.engine.raw_connection()
            cursor = connection.cursor()

            indexes = [
                # 复合索引：user_id + chat_id + postal_time
                """
                CREATE INDEX IF NOT EXISTS idx_tg_chat_history_user_chat
                ON tg_group_chat_history(user_id, chat_id, postal_time DESC)
                """,

                # 单列索引：user_id
                """
                CREATE INDEX IF NOT EXISTS idx_tg_chat_history_user_id
                ON tg_group_chat_history(user_id)
                """,

                # 单列索引：postal_time
                """
                CREATE INDEX IF NOT EXISTS idx_tg_chat_history_postal_time
                ON tg_group_chat_history(postal_time DESC)
                """,

                # 复合索引：chat_id + status
                """
                CREATE INDEX IF NOT EXISTS idx_tg_group_chat_id_status
                ON tg_group(chat_id, status)
                """
            ]

            for idx, sql in enumerate(indexes, 1):
                try:
                    cursor.execute(sql)
                    print(f"✅ 索引 {idx} 创建成功")
                except Exception as e:
                    print(f"⚠️  索引 {idx} 处理结果: {str(e)}")

            connection.commit()
            cursor.close()
            connection.close()

            print("\n✅ 所有索引创建完毕！")
            return True

        except Exception as e:
            print(f"❌ 创建索引失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = create_indexes()
    sys.exit(0 if success else 1)
