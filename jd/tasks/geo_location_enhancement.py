"""地理位置数据增强任务 - 为现有数据填充省份信息"""
import logging
from jd import db
from jd.tasks.base_task import BaseTask

logger = logging.getLogger(__name__)


class GeoLocationEnhancementTask(BaseTask):
    """地理位置数据增强任务，为现有地理位置记录填充省份信息"""

    name = "jd.geo_location_enhancement"

    def run(self, chat_id: int = None, batch_size: int = 100, **kwargs):
        """
        运行地理位置数据增强任务

        Args:
            chat_id: 可选，指定群组ID。如果为None，则处理所有群组
            batch_size: 每批处理的记录数
            **kwargs: 其他参数
        """
        try:
            from jd.services.geo_location_enhancement import GeoLocationEnhancementService

            logger.info(f"开始地理位置数据增强任务 - chat_id: {chat_id}, batch_size: {batch_size}")

            if chat_id:
                # 增强指定群组的记录
                stats = self._enhance_chat_geo_locations(chat_id, batch_size)
            else:
                # 增强所有群组的记录
                stats = self._enhance_all_geo_locations(batch_size)

            logger.info(f"地理位置数据增强任务完成: {stats}")
            return stats

        except Exception as e:
            logger.error(f"地理位置数据增强任务失败: {e}")
            raise

    def _enhance_chat_geo_locations(self, chat_id: int, batch_size: int) -> dict:
        """增强指定群组的地理位置记录"""
        try:
            from jd.models.ad_tracking_geo_location import AdTrackingGeoLocation

            stats = {
                'chat_id': chat_id,
                'total_processed': 0,
                'total_updated': 0,
                'errors': 0
            }

            # 查询该群组需要增强的记录
            records = AdTrackingGeoLocation.query.filter(
                AdTrackingGeoLocation.chat_id == chat_id,
                AdTrackingGeoLocation.city.isnot(None),
                AdTrackingGeoLocation.province.is_(None)
            ).limit(batch_size).all()

            for record in records:
                try:
                    # 通过城市名查找省份
                    province = self._get_province_by_city(record.city)
                    if province:
                        record.province = province
                        stats['total_updated'] += 1

                    stats['total_processed'] += 1

                except Exception as e:
                    logger.error(f"处理记录 {record.id} 失败: {e}")
                    stats['errors'] += 1
                    continue

            db.session.commit()
            return stats

        except Exception as e:
            logger.error(f"增强群组 {chat_id} 的地理位置记录失败: {e}")
            db.session.rollback()
            raise

    def _enhance_all_geo_locations(self, batch_size: int) -> dict:
        """增强所有群组的地理位置记录"""
        try:
            from jd.models.ad_tracking_geo_location import AdTrackingGeoLocation

            stats = {
                'total_processed': 0,
                'total_updated': 0,
                'errors': 0,
                'batch_count': 0
            }

            offset = 0
            has_more = True

            while has_more:
                # 查询一批需要增强的记录
                records = AdTrackingGeoLocation.query.filter(
                    AdTrackingGeoLocation.city.isnot(None),
                    AdTrackingGeoLocation.province.is_(None)
                ).offset(offset).limit(batch_size).all()

                if not records:
                    has_more = False
                    break

                stats['batch_count'] += 1
                batch_updated = 0

                for record in records:
                    try:
                        # 通过城市名查找省份
                        province = self._get_province_by_city(record.city)
                        if province:
                            record.province = province
                            batch_updated += 1

                        stats['total_processed'] += 1

                    except Exception as e:
                        logger.error(f"处理记录 {record.id} 失败: {e}")
                        stats['errors'] += 1
                        continue

                stats['total_updated'] += batch_updated
                offset += batch_size

                # 每批提交一次
                db.session.commit()
                logger.info(f"已处理批次 {stats['batch_count']}: 更新 {batch_updated}/{len(records)} 条记录")

            return stats

        except Exception as e:
            logger.error(f"增强所有地理位置记录失败: {e}")
            db.session.rollback()
            raise

    def _get_province_by_city(self, city_name: str) -> str:
        """通过城市名获取省份名"""
        try:
            from jd.models.ad_tracking_geo_location_master import AdTrackingGeoLocationMaster

            # 在地理位置主表中查找城市及其对应的省份
            result = db.session.execute("""
                SELECT p.name as province_name
                FROM ad_tracking_geo_location_master c
                JOIN ad_tracking_geo_location_master p ON c.parent_id = p.id
                WHERE c.name = :city_name AND c.level = 2 AND p.level = 1
                LIMIT 1
            """, {'city_name': city_name}).fetchone()

            return result.province_name if result else None

        except Exception as e:
            logger.error(f"通过城市名 {city_name} 查找省份失败: {e}")
            return None