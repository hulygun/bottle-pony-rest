import json
import os

import math
from bottle import response, request
from pony.orm import db_session, perm, commit

PREFIX = os.getenv('API_START','/')

class BaseResourceView(object):
  allowed_methods = ['GET']
  per_page = 10
  perm_mode = 'view'
  perm_group = 'anybody'
  resource = None
  endpoint = None
  db = None

  def __init__(self, app):
    self.setup_routing(app)

  def set_object_link(self, obj):
    prefix = PREFIX
    obj['link'] = '{}{}/{}'.format(prefix, self.get_endpoint(), obj['id'])
    return obj

  def prepare_objects(self, queryset, pk):
    pre = json.loads(queryset.to_json())['objects'][self.resource.__name__]
    if pk:
      pre = pre[pk]
    else:
      pre = [self.set_object_link(v) for k, v in pre.items()]
    return pre

  def get_endpoint(self):
    """
    Get endpoint name from endpoint property or resource class name
    :rtype: str
    """
    if not self.endpoint:
      self.endpoint = self.resource.__name__.lower()
    return self.endpoint

  @db_session
  def render_to_response(self, pk=None):
    """
    Return data
    :param pk: primary key of resource object
    :rtype: json
    """
    response.content_type = 'application/json'
    method = request.method
    if method in self.allowed_methods:
      with self.db.set_perms_for(self.resource):
        perm(self.perm_mode, group=self.perm_group)
        data = getattr(self, method.lower())(pk)
        return json.dumps(data)

  def build_routes(self):
    """
    Build routes for instance
    :rtype: list of tuples(route, allowed_methods)
    """
    allowed_methods = self.allowed_methods
    result = []
    route, methods = self.get_endpoint(), ['GET']
    if 'POST' in allowed_methods:
      methods.append('POST')
    result.append(('/' + route, methods))
    result.append(('/' + route + '/<pk>', [m for m in allowed_methods if m != 'POST']))
    print('build routes', result)
    return result

  def setup_routing(self, app):
    """
    Setup routes to bottle instance
    :param app: obj Bottle instance
    """
    print('setup routing')
    for route, methods in self.build_routes():
      app.route(route, methods, self.render_to_response)

  def default_data(self, pk):
    data = {'data': None}
    if not pk and request.method == 'GET':
      data['per_page'] = self.per_page
      data['pages_count'] = None
      data['current'] = None
      data['next'] = None
      data['prev'] = None
    return data

  def get(self, pk):
    data = self.default_data(pk)
    if pk:
      data['data'] = self.prepare_objects(self.resource.get(id=pk), pk)
    else:
      result = self.resource.select()
      page = int(request.GET.get('page', 1))
      count = result.count()
      result = result.page(page, self.per_page)
      num_pages = math.ceil(count / self.per_page)
      data['pages_count'] = num_pages
      data['current'] = page
      if page < num_pages:
        data['next'] = '{}{}?page={}'.format(PREFIX, self.get_endpoint(), (page + 1))
      if page > 1:
        data['prev'] = '{}{}?page={}'.format(PREFIX, self.get_endpoint(), (page - 1))
      data['data'] = self.prepare_objects(result, pk)
    return data

  def post(self, pk):
    data = self.default_data(pk=None)
    obj = self.resource(**request.json)
    commit()
    data['data'] = self.prepare_objects(obj, None)
    return data

  def put(self, pk):
    data = self.default_data(pk)
    data['data'] = self.resource.get(id=pk)
    return data

  def delete(self, pk):
    data = self.default_data(pk)
    data['data'] = self.resource.get(id=pk).delete()
    return data
