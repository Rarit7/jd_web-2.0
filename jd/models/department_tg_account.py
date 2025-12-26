"""
部门-TG账户关联模型 - 多对多关系表
"""
from jd import db


class DepartmentTgAccount(db.Model):
    __tablename__ = 'department_tg_account'

    id = db.Column(db.Integer, primary_key=True, comment='主键ID')
    department_id = db.Column(db.Integer, db.ForeignKey('department.id', ondelete='CASCADE'),
                             nullable=False, comment='部门ID')
    tg_user_id = db.Column(db.String(128), nullable=False, comment='TG账户的user_id')
    created_at = db.Column(db.DateTime, default=db.func.now(), comment='创建时间')
    created_by = db.Column(db.Integer, db.ForeignKey('secure_user.id', ondelete='SET NULL'),
                          nullable=True, comment='创建人(secure_user.id)')

    # 唯一约束（部门-TG账户组合唯一）
    __table_args__ = (
        db.UniqueConstraint('department_id', 'tg_user_id', name='uk_dept_tg'),
        db.Index('idx_department', 'department_id'),
        db.Index('idx_tg_user', 'tg_user_id'),
    )

    # 关系定义
    creator = db.relationship('SecureUser', foreign_keys=[created_by])

    @staticmethod
    def get_departments_by_tg_user_id(tg_user_id):
        """根据TG账户ID获取关联的所有部门ID列表"""
        relations = DepartmentTgAccount.query.filter_by(tg_user_id=str(tg_user_id)).all()
        return [rel.department_id for rel in relations]

    @staticmethod
    def get_tg_user_ids_by_department(department_id):
        """根据部门ID获取关联的所有TG账户user_id列表"""
        relations = DepartmentTgAccount.query.filter_by(department_id=department_id).all()
        return [rel.tg_user_id for rel in relations]

    @staticmethod
    def add_relation(department_id, tg_user_id, created_by=None):
        """添加部门-TG账户关联"""
        existing = DepartmentTgAccount.query.filter_by(
            department_id=department_id,
            tg_user_id=str(tg_user_id)
        ).first()

        if existing:
            return existing

        relation = DepartmentTgAccount(
            department_id=department_id,
            tg_user_id=str(tg_user_id),
            created_by=created_by
        )
        return relation

    @staticmethod
    def remove_relation(department_id, tg_user_id):
        """删除部门-TG账户关联"""
        relation = DepartmentTgAccount.query.filter_by(
            department_id=department_id,
            tg_user_id=str(tg_user_id)
        ).first()
        return relation

    @staticmethod
    def replace_department_relations(department_id, tg_user_ids, created_by=None):
        """替换部门的所有TG账户关联（先删除旧的，再添加新的）

        Args:
            department_id: 部门ID
            tg_user_ids: TG账户user_id列表
            created_by: 创建人ID

        Returns:
            新创建的关联记录列表
        """
        # 删除该部门的所有旧关联
        DepartmentTgAccount.query.filter_by(department_id=department_id).delete()

        # 添加新关联
        new_relations = []
        for tg_user_id in tg_user_ids:
            relation = DepartmentTgAccount(
                department_id=department_id,
                tg_user_id=str(tg_user_id),
                created_by=created_by
            )
            new_relations.append(relation)
            db.session.add(relation)

        return new_relations

    def to_dict(self):
        """转换为字典格式"""
        data = {
            'id': self.id,
            'department_id': self.department_id,
            'tg_user_id': self.tg_user_id,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'created_by': self.created_by,
        }

        # 如果有关联的部门信息，也一并返回
        if hasattr(self, 'department') and self.department:
            data['department_name'] = self.department.name

        return data

    def __repr__(self):
        return f'<DepartmentTgAccount dept={self.department_id} tg={self.tg_user_id}>'
