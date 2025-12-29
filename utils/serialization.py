# Import libraries
import yaml

# Class 'QuotedDumper'
class QuotedDumper(yaml.SafeDumper):
    """ Class description """

    # Function 'dumpyaml'
    @staticmethod
    def quotedstr(dumper, data):
        """ Function description """
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')

    # Function 'dumpyaml'
    @staticmethod
    def quotednone(dumper, _):
        """ Function description """
        return dumper.represent_scalar('tag:yaml.org,2002:null', 'Null')

    # Function 'dumpyaml'
    @staticmethod
    def quotedbool(dumper, data):
        """ Function description """
        return dumper.represent_scalar('tag:yaml.org,2002:bool', 'True' if data else 'False')

    # Function 'dumpyaml'
    @classmethod
    def register(cls):
        """ Function description """
        cls.add_representer(str, cls.quotedstr)
        cls.add_representer(type(None), cls.quotednone)
        cls.add_representer(bool, cls.quotedbool)

    # Function 'dumpyaml'
    @classmethod
    def dumpyaml(cls, filepath, data):
        """ Function description """
        cls.register()
        with open(filepath, 'w') as f:
            yaml.dump(data, f, sort_keys=False, Dumper=cls)
