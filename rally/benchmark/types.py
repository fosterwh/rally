# Copyright (C) 2014 Yahoo! Inc. All Rights Reserved.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import abc
import operator
import re

from rally import exceptions


def set(**kwargs):
    """Decorator to define resource transformation(s) on scenario parameters.

    The `kwargs` passed as arguments to the decorator are used to
    map a key in the scenario config to the subclass of ResourceType
    used to perform a transformation on the value of that key.
    """
    def wrapper(func):
        func.preprocessors = getattr(func, 'preprocessors', {})
        func.preprocessors.update(kwargs)
        return func
    return wrapper


class ResourceType(object):

    @classmethod
    @abc.abstractmethod
    def transform(cls, clients, resource_config):
        """Transform the resource.

        :param clients: openstack admin client handles
        :param resource_config: scenario config of resource

        :returns: transformed value of resource
        """


def _id_from_name(resource_config, resources, typename):
    """Return the id of the resource whose name matches the pattern.

    When resource_config contains `name`, an exact match is used.
    When resource_config contains `regex`, a pattern match is used.

    An `InvalidScenarioArgument` is thrown if the pattern does
    not match unambiguously.

    :param resource_config: resource to be transformed
    :param resources: iterable containing all resources
    :param typename: name which describes the type of resource

    :returns: resource id uniquely mapped to `name` or `regex`
    """
    if resource_config.get('name'):
        patternstr = "^{0}$".format(resource_config.get('name'))
    elif resource_config.get('regex'):
        patternstr = resource_config.get('regex')
    else:
        raise exceptions.InvalidScenarioArgument(
            "{typename} 'id', 'name', or 'regex' not found "
            "in '{resource_config}' ".format(typename=typename.title(),
                                             resource_config=resource_config))

    pattern = re.compile(patternstr)
    matching = filter(lambda resource: re.search(pattern, resource.name),
                      resources)
    if not matching:
        raise exceptions.InvalidScenarioArgument(
            "{typename} with pattern '{pattern}' not found".format(
                typename=typename.title(), pattern=pattern.pattern))
    elif len(matching) > 1:
        raise exceptions.InvalidScenarioArgument(
            "{typename} with name '{pattern}' is ambiguous, possible matches "
            "by id: {ids}".format(typename=typename.title(),
                                  pattern=pattern.pattern,
                                  ids=", ".join(map(operator.attrgetter("id"),
                                                    matching))))
    return matching[0].id


class FlavorResourceType(ResourceType):

    @classmethod
    def transform(cls, clients, resource_config):
        """Transform the resource config to id.

        :param clients: openstack admin client handles
        :param resource_config: scenario config with `id`, `name` or `regex`

        :returns: id matching resource
        """
        resource_id = resource_config.get('id')
        if not resource_id:
            novaclient = clients.nova()
            resource_id = _id_from_name(resource_config=resource_config,
                                        resources=novaclient.flavors.list(),
                                        typename='flavor')
        return resource_id


class ImageResourceType(ResourceType):

    @classmethod
    def transform(cls, clients, resource_config):
        """Transform the resource config to id.

        :param clients: openstack admin client handles
        :param resource_config: scenario config with `id`, `name` or `regex`

        :returns: id matching resource
        """
        resource_id = resource_config.get('id')
        if not resource_id:
            glanceclient = clients.glance()
            resource_id = _id_from_name(resource_config=resource_config,
                                        resources=glanceclient.images.list(),
                                        typename='image')
        return resource_id
