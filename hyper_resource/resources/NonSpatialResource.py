import hashlib
import json
from copy import deepcopy

from hyper_resource.resources.AbstractResource import AbstractResource, RequiredObject
from rest_framework.response import Response


class NonSpatialResource(AbstractResource):

    def operation_name_method_dic(self):
        return super(NonSpatialResource, self).operation_name_method_dic()

    # same signature in FeatureResource
    def response_request_attributes_functions_str_with_url(self, attributes_functions_str, request=None):
        pass

    def required_object_for_simple_path(self, request):
        # django context object is required when the serializer has HyperlinkedrelatedField
        serializer = self.serializer_class(self.object_model, context={'request': request})
        return RequiredObject(serializer.data, self.content_type_by_accept(request), self.object_model, 200)

    def get_objects_from_join_operation(self, request, attributes_functions_str):
        join_operation = self.build_join_operation(request, attributes_functions_str)

        if type(join_operation.right_join_data) == list:
            return self.join_dict_list_on_non_spatial_resource(join_operation)
        return self.join_dict_on_non_spatial_resource(join_operation)

    def join_dict_on_non_spatial_resource(self, join_operation):
        if join_operation.left_join_data[ join_operation.left_join_attr ] != join_operation.right_join_data[ join_operation.right_join_attr ]:
            return None

        join_operation.left_join_data["__joined__"] = []
        join_operation.left_join_data["__joined__"].append( join_operation.right_join_data )
        return join_operation.left_join_data

    def join_dict_list_on_non_spatial_resource(self, join_operation):
        join_operation.left_join_data['__joined__'] = []

        for dicti in join_operation.right_join_data:
            if join_operation.left_join_data[ join_operation.left_join_attr ] == dicti[ join_operation.right_join_attr ]:
                join_operation.left_join_data['__joined__'].append(dicti)

        if len(join_operation.left_join_data['__joined__']) == 0:
            return None
        return join_operation.left_join_data

    '''
    def join_non_spatial_on_feature(self, join_operation):
        if join_operation.left_join_data[ join_operation.left_join_attr] != \
        join_operation.right_join_data['properties'][ join_operation.right_join_attr]:
            return None

        for alpha_attr, alpha_data in join_operation.left_join_data.items():
            join_operation.right_join_data['properties']['joined__' + alpha_attr] = alpha_data

        return join_operation.right_join_data

    def join_non_spatial_on_feature_collection(self, join_operation):
        for feature in join_operation.right_join_data['features']:
            if join_operation.left_join_data[ join_operation.left_join_attr] == \
                feature['properties'][ join_operation.right_join_attr]:

                copied_feature = deepcopy(feature)
                for alpha_attr, alpha_data in join_operation.left_join_data.items():
                    copied_feature['properties']['joined__' + alpha_attr] = alpha_data
                return copied_feature # only one location joined on alphanumeric data
    '''

    # todo: refactor 'response_request_with_attributes()' of the other classes to implement to behaviour of get_objects_serialized_by_only_attributes
    '''
    def response_request_with_attributes(self, attributes_functions_name, request=None):
        a_dict = {}
        attributes = attributes_functions_name.strip().split(',')

        for attr_name in attributes:
            obj = self._value_from_object(self.object_model, attr_name, [])
            a_dict[attr_name] = obj

        self.current_object_state = a_dict
    '''

    def basic_get(self, request, *args, **kwargs):
        self.object_model = self.get_object(kwargs)
        self.current_object_state = self.object_model
        self.set_basic_context_resource(request)
        attributes_functions_str = kwargs.get(self.attributes_functions_name_template())

        if self.is_simple_path(attributes_functions_str):
            return self.required_object_for_simple_path(request)
        elif self.path_has_only_attributes(attributes_functions_str):
            return self.required_object_for_only_attributes(request, attributes_functions_str)

        res = self.get_required_object_from_method_to_execute(request, attributes_functions_str)
        if res is None:
            return self.required_object_for_invalid_sintax(attributes_functions_str)
        return res

    def resource_type_by_only_attributes(self, request, attributes_functions_str):
        r_type = self.resource_type_or_default_resource_type(request)
        if r_type != self.default_resource_type():
            return r_type

        attrs_functs_arr = self.remove_last_slash(attributes_functions_str).split(',')
        if len(attrs_functs_arr) == 1:
            # the field type has priority over default resource type
            return type(self.field_for(attrs_functs_arr[0]))

        return self.default_resource_type()

    def options(self, request, *args, **kwargs):
        required_object = self.basic_options(request, *args, **kwargs)
        if required_object.status_code == 200:
            response = Response(required_object.representation_object, content_type=required_object.content_type, status=200)
            self.add_options_headers(request, response)
        else:
            response = Response(data={"This request is not supported": self.kwargs.get("attributes_functions", None)},
                                status=required_object.status_code)
        return response