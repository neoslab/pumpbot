# Import libraries
import asyncio
import platform


# Class 'EventLoopConf'
class EventLoopConf:
    """ Class description """

    # Function 'WaitForToken'
    @staticmethod
    def importlib():
        if platform.system() != "Windows":
            try:
                # noinspection PyPackageRequirements
                import uvloop
                asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
            except ImportError:
                pass
