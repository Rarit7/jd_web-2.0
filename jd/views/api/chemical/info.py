from io import BytesIO

import pandas as pd
from flask import request, make_response, session, jsonify

from jd.models.chemical_platform import ChemicalPlatform
from jd.models.chemical_platform_product_info import ChemicalPlatformProductInfo
from jd.services.chemical import ChemicalPlatformService
from jd.services.role_service.role import ROLE_SUPER_ADMIN, RoleService
from jd.tasks.first.spider_chemical import deal_spider_chemical
from jd.views import get_or_exception, success, APIException
from jd.views.api import api
from jd import db


@api.route('/chemical/product/info/list', methods=['GET'], roles=[ROLE_SUPER_ADMIN])
def chemical_product_info_list():
    """
    获取产品列表
    :return:
    """
    args = request.args
    page = get_or_exception('page', args, 'int', 1)
    page_size = get_or_exception('page_size', args, 'int', 20)
    search_product_name = get_or_exception('search_product_name', args, 'str', '')
    search_compound_name = get_or_exception('search_compound_name', args, 'str', '')
    search_contact_number = get_or_exception('search_contact_number', args, 'str', '')
    search_platform_id_list = args.getlist('search_platform_id', int)

    offset = (page - 1) * page_size
    query = ChemicalPlatformProductInfo.query
    if search_platform_id_list:
        query = query.filter(ChemicalPlatformProductInfo.platform_id.in_(search_platform_id_list))
    if search_product_name:
        query = query.filter(ChemicalPlatformProductInfo.product_name.like('%' + search_product_name + '%'))
    if search_compound_name:
        query = query.filter(ChemicalPlatformProductInfo.compound_name.like('%' + search_compound_name + '%'))
    if search_contact_number:
        query = query.filter(ChemicalPlatformProductInfo.contact_number.like('%' + search_contact_number + '%'))
    product_info_list = query.order_by(ChemicalPlatformProductInfo.id.desc()).offset(
        offset).limit(page_size).all()
    total_records = query.count()
    data = [
        {
            'id': item.id,
            'platform_name': ChemicalPlatformService.PLATFORM_MAP[item.platform_id],
            'product_name': item.product_name,
            'compound_name': item.compound_name,
            'seller_name': item.seller_name,
            'contact_number': item.contact_number,
            'created_at': item.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for item in product_info_list
    ]
    total_pages = (total_records + page_size - 1) // page_size
    platform_list = [{'id': k, 'name': v} for k, v in ChemicalPlatformService.PLATFORM_MAP.items()]
    
    return jsonify({
        'err_code': 0,
        'err_msg': '',
        'payload': {
            'data': data,
            'platform_list': platform_list,
            'total_pages': total_pages,
            'current_page': page,
            'total_records': total_records,
            'page_size': page_size
        }
    })


@api.route('/chemical/product/info/search', methods=['POST'])
def chemical_product_info_search():
    """
    搜索产品
    :return:
    """
    args = request.json
    platform_id = get_or_exception('platform_id', args, 'int')
    deal_spider_chemical.delay(platform_id)
    return success()


@api.route('/chemical/product/info/delete', methods=['GET'])
def chemical_product_info_delete():
    """
    删除产品
    :return:
    """
    args = request.args
    id = get_or_exception('id', args, 'int')
    ChemicalPlatformProductInfo.query.filter_by(id=id).delete()
    return success({'message': '产品删除成功'})


@api.route('/chemical/product/info/download', methods=['GET'])
def chemical_product_info_download():
    args = request.args
    search_platform_id = get_or_exception('search_platform_id', args, 'int', 0)
    search_product_name = get_or_exception('search_product_name', args, 'str', '')
    search_compound_name = get_or_exception('search_compound_name', args, 'str', '')
    query = ChemicalPlatformProductInfo.query
    if search_platform_id:
        query = query.filter(ChemicalPlatformProductInfo.platform_id == search_platform_id)
    if search_product_name:
        query = query.filter(ChemicalPlatformProductInfo.product_name.like('%' + search_product_name + '%'))
    if search_compound_name:
        query = query.filter(ChemicalPlatformProductInfo.compound_name.like('%' + search_compound_name + '%'))
    product_info_list = query.order_by(ChemicalPlatformProductInfo.id.desc()).all()
    data = [
        {
            '平台': ChemicalPlatformService.PLATFORM_MAP[item.platform_id],
            '产品名称': item.product_name,
            '化合物名称': item.compound_name,
            '商家名称': item.seller_name,
            '联系方式': item.contact_number,
        } for item in product_info_list]

    # 创建DataFrame
    columns = ['平台', '产品名称', '化合物名称', '商家名称', '联系方式']
    df = pd.DataFrame(data, columns=columns)

    # 将DataFrame保存到Excel文件
    output = BytesIO()
    df.to_csv(output, index=False, encoding='utf-8')

    # 设置响应头
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=product.csv"
    response.headers["Content-type"] = "text/csv"

    return response


# REST API endpoints for frontend integration
@api.route('/chemical-products', methods=['GET'])
def get_chemical_products():
    """获取化工产品列表 - REST API"""
    args = request.args
    page = get_or_exception('page', args, 'int', 1)
    page_size = get_or_exception('page_size', args, 'int', 20)
    search_product_name = get_or_exception('search_product_name', args, 'str', '')
    search_compound_name = get_or_exception('search_compound_name', args, 'str', '')
    search_contact_number = get_or_exception('search_contact_number', args, 'str', '')
    search_platform_id_list = args.getlist('search_platform_id', int)

    offset = (page - 1) * page_size
    query = ChemicalPlatformProductInfo.query
    if search_platform_id_list:
        query = query.filter(ChemicalPlatformProductInfo.platform_id.in_(search_platform_id_list))
    if search_product_name:
        query = query.filter(ChemicalPlatformProductInfo.product_name.like('%' + search_product_name + '%'))
    if search_compound_name:
        query = query.filter(ChemicalPlatformProductInfo.compound_name.like('%' + search_compound_name + '%'))
    if search_contact_number:
        query = query.filter(ChemicalPlatformProductInfo.contact_number.like('%' + search_contact_number + '%'))
    
    product_info_list = query.order_by(ChemicalPlatformProductInfo.id.desc()).offset(
        offset).limit(page_size).all()
    total_records = query.count()
    
    data = [{
        'id': item.id,
        'platform_id': item.platform_id,
        'platform_name': ChemicalPlatformService.PLATFORM_MAP.get(item.platform_id, '未知平台'),
        'product_name': item.product_name,
        'compound_name': item.compound_name,
        'seller_name': item.seller_name,
        'contact_number': item.contact_number,
        'status': item.status,
        'created_at': item.created_at.isoformat() if item.created_at else None,
        'updated_at': item.updated_at.isoformat() if item.updated_at else None,
    } for item in product_info_list]
    
    platform_list = [{'id': k, 'name': v} for k, v in ChemicalPlatformService.PLATFORM_MAP.items()]
    
    return success({
        'data': data,
        'total_records': total_records,
        'total_pages': (total_records + page_size - 1) // page_size,
        'current_page': page,
        'page_size': page_size,
        'platform_list': platform_list
    })


@api.route('/chemical-products/<int:product_id>', methods=['DELETE'])
def delete_chemical_product(product_id):
    """删除化工产品 - REST API"""
    product = ChemicalPlatformProductInfo.query.filter_by(id=product_id).first()
    
    if not product:
        raise APIException('产品不存在')
    
    ChemicalPlatformProductInfo.query.filter_by(id=product_id).delete()
    db.session.commit()
    
    return success(None)


@api.route('/chemical-products/download', methods=['GET'])
def download_chemical_products():
    """下载化工产品数据 - REST API"""
    args = request.args
    search_platform_id = get_or_exception('search_platform_id', args, 'int', 0)
    search_product_name = get_or_exception('search_product_name', args, 'str', '')
    search_compound_name = get_or_exception('search_compound_name', args, 'str', '')
    
    query = ChemicalPlatformProductInfo.query
    if search_platform_id:
        query = query.filter(ChemicalPlatformProductInfo.platform_id == search_platform_id)
    if search_product_name:
        query = query.filter(ChemicalPlatformProductInfo.product_name.like('%' + search_product_name + '%'))
    if search_compound_name:
        query = query.filter(ChemicalPlatformProductInfo.compound_name.like('%' + search_compound_name + '%'))
    
    product_info_list = query.order_by(ChemicalPlatformProductInfo.id.desc()).all()
    data = [{
        '平台': ChemicalPlatformService.PLATFORM_MAP.get(item.platform_id, '未知平台'),
        '产品名称': item.product_name,
        '化合物名称': item.compound_name,
        '商家名称': item.seller_name,
        '联系方式': item.contact_number,
    } for item in product_info_list]

    # 创建DataFrame
    columns = ['平台', '产品名称', '化合物名称', '商家名称', '联系方式']
    df = pd.DataFrame(data, columns=columns)

    # 将DataFrame保存到CSV文件
    output = BytesIO()
    df.to_csv(output, index=False, encoding='utf-8')

    # 设置响应头
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=chemical_products.csv"
    response.headers["Content-type"] = "text/csv"

    return response


@api.route('/chemical-products/search', methods=['POST'])
def start_chemical_product_search():
    """启动化工产品抓取 - REST API"""
    args = request.json
    platform_id = get_or_exception('platform_id', args, 'int')
    
    deal_spider_chemical.delay(platform_id)
    return success(None)
