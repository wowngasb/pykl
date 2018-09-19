# coding: utf-8

import graphene as g

from pykl.tiny.grapheneinfo import (
    BuildType, 
    BuildArgument, 
    SQLAlchemyObjectType, 
    List, 
    NonNull, 
    Field
)

from pykl.tiny.grapheneinfo.utils import (
    BitMask,
    HiddenField,
    InitializeField,
    EditableField,
    SortableField,
    CustomField,
    upper_tuple,
    mask_field,
    mask_keys,
)

from sqlalchemy.dialects.mysql import INTEGER

from sqlalchemy import (
    Index, 
    types, 
    Column, 
    BigInteger, 
    Integer, 
    SmallInteger, 
    String, 
    Text, 
    DateTime, 
    Float, 
    Numeric, 
    text, 
    TIMESTAMP,
)

StateEnum = g.Enum('StateEnum', upper_tuple({'unknown': 0, 'normal': 1, 'frozen': 2, 'notdel': 3, 'deleted': 4, 'expired': 8, 'reserve': 16}), description=u'通用状态类型 0:未知(用于检索所有) UNKNOWN,  1:正常 NORMAL,  2:冻结 FROZEN,  3:非删除 NOTDEL,  4:删除 DELETED,  8:过期 EXPIRED,  16:备用 RESERVE')

SortDirectionEnum = g.Enum('SortDirectionEnum', upper_tuple(['asc', 'desc']), description=u'排序方向 asc:升序 ASC, desc:降序 DESC')

class SortOption(g.InputObjectType):
    field = Field(g.String, description=u'允许排序字段')
    direction = Field(SortDirectionEnum, description=u'排序方向')

class IntRange(g.InputObjectType):
    lower = Field(g.Int, description=u'整数 下限 小于等于')
    upper = Field(g.Int, description=u'整数 上限 大于等于')

class FloatRange(g.InputObjectType):
    lower = Field(g.Float, description=u'浮点数 下限 小于等于')
    upper = Field(g.Float, description=u'浮点数 上限 大于等于')

class DateRange(g.InputObjectType):
    lower = Field(g.String, description=u'日期字符串 Y-m-d H:i:s 下限 小于等于')
    upper = Field(g.String, description=u'日期字符串 Y-m-d H:i:s 上限 大于等于')

class TimeRange(g.InputObjectType):
    lower = Field(g.String, description=u'时间字符串 H:i:s 下限 小于等于')
    upper = Field(g.String, description=u'时间字符串 H:i:s 上限 大于等于')

class DayRange(g.InputObjectType):
    lower = Field(g.String, description=u'日期字符串 Y-m-d 下限 小于等于')
    upper = Field(g.String, description=u'日期字符串 Y-m-d 上限 大于等于')

class OutSortOption(g.ObjectType):
    field = Field(g.String, description=u'允许排序字段', required=True)
    direction = Field(SortDirectionEnum, description=u'排序方向', required=True)

class PageInfo(g.ObjectType):
    u'''分页信息'''
    num = g.Int(description=u'每页数量', required=True)
    total = g.Int(description=u'总数', required=True)
    page = g.Int(description=u'当前页数', required=True)
    hasNextPage = g.Boolean(description=u'是否拥有下一页', required=True)
    hasPreviousPage = g.Boolean(description=u'是否拥有上一页', required=True)

    sortOption = Field(OutSortOption, description=u'排序选项', required=True)
    allowSortField = List(g.String, description=u'允许排序的字段', required=True)

    @classmethod
    def buildPageInfo(cls, total=0, num=0, page=1, sortOption=None, allowSortField=None):
        total = 0 if (not total or total < -1) else num
        num = 10 if not num or num <= 0 else num
        page = 1 if not page or page <= 0 else page

        return PageInfo(
            num=num,
            page=page,
            total=total,
            hasPreviousPage=not page==1,
            hasNextPage= (total > page * num or total == -1),
            sortOption=OutSortOption(field=sortOption.field, direction=sortOption.direction) if allowSortField else OutSortOption(field='', direction='asc'),
            allowSortField=allowSortField if allowSortField else [],
        )