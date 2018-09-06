from hyper_resource.models import CollectionResourceOperationController
from hyper_resource.resources.AbstractCollectionResource import AbstractCollectionResource
from copy import deepcopy

class CollectionResource(AbstractCollectionResource):
    def __init__(self):
        super(CollectionResource, self).__init__()
        self.queryset = None
        self.operation_controller = CollectionResourceOperationController()
        self.objs_per_page = 1000

    def add_base_headers(self, request, response):
        super(AbstractCollectionResource, self).add_base_headers(request, response)
        attributes_functions_str = self.kwargs.get('attributes_functions') if self.kwargs.get('attributes_functions') is not None else ""
        attrs_funcs_str = self.remove_projection_from_path(attributes_functions_str) if self.path_has_projection(attributes_functions_str) else attributes_functions_str

        if  self.is_simple_path(attrs_funcs_str) or\
            self.get_operation_name_from_path(attrs_funcs_str) == self.operation_controller.offset_limit_collection_operation_name:

            pagination_link = self.build_offset_limit_link(request, attrs_funcs_str)
            self.add_url_in_header(pagination_link, response, rel="next")

    def build_offset_limit_link(self, request, attributes_functions_str):
        absolute_uri = self.remove_last_slash(request.build_absolute_uri())
        offset_limit_oper_name = self.operation_controller.offset_limit_collection_operation_name

        if not self.is_simple_path(attributes_functions_str): # if isn't simple path, is offset_limit operation
            offset_limit_arr = self.remove_last_slash(attributes_functions_str).split("/")
            range_arr = offset_limit_arr[1].split("&")
            new_start_idx = str( int(range_arr[0]) + self.objs_per_page)
            new_offset_limit = offset_limit_arr[0] + "/" + new_start_idx + "&" + range_arr[1]
            pagination_link = absolute_uri[:absolute_uri.index(offset_limit_oper_name)] + new_offset_limit
        else:
            pagination_link = absolute_uri + "/" + offset_limit_oper_name + "/" + str(self.objs_per_page +1 ) + "&" + str(self.objs_per_page)

        return pagination_link

    def define_resource_type_by_collect_operation(self, request, attributes_functions_str):
        return self.resource_type_or_default_resource_type(request)

    def operations_with_parameters_type(self):
        return self.operation_controller.collection_operations_dict()

    def get_objects_from_spatialize_operation(self, request, attributes_functions_str):
        spatialize_operation = self.build_spatialize_operation(request, attributes_functions_str)
        return self.join_dict_list_on_spatial_collection(spatialize_operation)

    def join_dict_list_on_spatial_collection(self, spatialize_operation):
        spatialized_data_list = []
        for original_feature in spatialize_operation.right_join_data['features']:
            updated_feature = deepcopy(original_feature)
            for position, dict_to_spatialize in enumerate(spatialize_operation.left_join_data):
                if updated_feature['properties'][spatialize_operation.right_join_attr] == dict_to_spatialize[spatialize_operation.left_join_attr]:
                    updated_feature['properties']['joined__' + str(position) ] = deepcopy(dict_to_spatialize)#.pop(position)

            if sorted(list(updated_feature['properties'].keys())) != sorted(list(original_feature['properties'].keys())):
                spatialized_data_list.append(updated_feature)

        return {'type': 'FeatureCollection', 'features': spatialized_data_list}

    def get_objects_serialized(self):
        objects = self.model_class().objects.all()
        return self.serializer_class(objects, many=True, context={'request': self.request}).data

    def get_objects_by_only_attributes(self, attribute_names_str):
        attribute_names_str_as_array = self.remove_last_slash(attribute_names_str).split(',')
        return self.model_class().objects.values(*attribute_names_str_as_array)

    def get_objects_serialized_by_only_attributes(self, attribute_names_str, query_set):
        arr = []
        attribute_names_str_as_array = self.remove_last_slash(attribute_names_str).split(',')

        for obj in query_set:
            a_dic = {}

            for att_name in attribute_names_str_as_array:
                a_dic[att_name] = obj[att_name]

            arr.append(a_dic)

        return arr

    def get_objects_from_specialized_operation(self, attributes_functions_str):
        return self.get_objects_from_filter_operation(attributes_functions_str)

    def get_objects_by_functions(self, attributes_functions_str):
        objects = []

        if self.path_has_filter_operation(attributes_functions_str):
            objects = self.get_objects_from_filter_operation(attributes_functions_str)

        return objects

    def get_context_for_offset_limit_operation(self, request, attributes_functions_str):
        context = {}
        return context

    def get_objects_from_simple_path(self):
        if self.model_class().objects.count() > self.objs_per_page:
            return self.model_class().objects.all()[0:self.objs_per_page]

        return self.model_class().objects.all()
