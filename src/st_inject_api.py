import logging
import threading
from typing import Any, Dict, Iterable, Optional, Union
from tornado.routing import Rule, Matcher
from typing import (
    cast,
)

_global_tornado_hook = None
_global_hook_lock = threading.RLock()

class CustomRule:
    def __init__(self, path_pattern: Union[str, Matcher], handler_class: Any,
                 target_kwargs: Optional[Dict[str, Any]] = None, name: Optional[str] = None,):
        self.path_pattern = path_pattern
        self.handler_class = handler_class
        self.target_kwargs = target_kwargs
        self.name = name

def init_global_tornado_hook(rule_list: Iterable[Union[CustomRule, Rule]]):
    """
    Injects custom RESTful routes into the Streamlit application by intercepting the underlying Tornado web framework.
    
    This function serves as a mechanism to add custom behavior to a Streamlit application without modifying its core logic.
    It ensures that the custom routes are injected only once, and that the native behavior of Streamlit is preserved for 
    other routes.

    Calling this function twice has no effect. To change the rule list,
    first call 'uninitialize_global_tornado_hook' and then call this function again with the new rule list.
    
    Example:
        >>> from src.hooks.injectApi import init_global_tornado_hook, CustomRule
        >>> from tornado.web import RequestHandler
        >>> class CustomHelloWorldHandler(RequestHandler):
        >>>     def get(self):
        >>>         self.write({
        >>>             "text": "Hello World"
        >>>         })
        >>> init_global_tornado_hook([ CustomRule("/hello", CustomHelloWorldHandler) ])

    Args:
        rule_list (Iterable[Union[CustomRule, Rule]]): A list of custom rules to inject into the Streamlit application.
    Returns:
        TRUE if the hooking mechanism was executed successfully, FALSE otherwise.
    """

    # How this function works:
    # 1. The global object '_global_tornado_hook' ensures the hooking mechanism is executed only once.
    # 3. A list 'injected_rule_list' is prepared containing custom routing rules based on the given 'rule_list'.
    # 4. A custom version of the 'find_handler' method is defined. This method checks if the current Tornado 
    #    Application instance has been hooked. If not, it injects the custom rules.
    # 5. All requests are then forwarded to the original 'find_handler' method, ensuring that Streamlit's 
    #    native behavior remains unaffected.
    # 6. Next, the custom 'find_handler' method is injected into Tornado's Application class, overriding 
    #    its default behavior.
    # 7. There is also a 'TornadoHook' class that can be used to unhook the application. 
    # This interception allows the addition of custom RESTful routes to Streamlit without affecting its core routes.

    import tornado.web
    from tornado import httputil
    from tornado.routing import Rule, PathMatches, RuleRouter
    from tornado.web import Application, RequestHandler
    global _global_tornado_hook

    if rule_list is None or len(rule_list) == 0:
        return False
    
    with _global_hook_lock:
        if _global_tornado_hook:
            return False
    
    # Convert the rule list to a list of Rule objects
    injected_rule_list = [ Rule(matcher=PathMatches(rule.path_pattern), target=rule.handler_class,
                                target_kwargs=rule.target_kwargs, name=rule.name)
                          if isinstance(rule, CustomRule) else rule for rule in rule_list ]
    
    hooked_applications = set()
    original_find_handler = tornado.web.Application.find_handler

    custom_router = RuleRouter(injected_rule_list)

    class CustomApplication:
        # Note that self here is not CustomApplication but Application
        def find_handler(
            self: Application, request: httputil.HTTPServerRequest, **kwargs: Any
        ):
            # Logging
            #print("CustomApplication.find_handler" + str(request))

            if not self in hooked_applications:
                # Self is the Application object
                hooked_applications.add(self)

                # Hook the application
                # for rule in reversed(injected_rule_list):
                #     # Insert the rule at the beginning of the list
                #     self.default_router.rules.insert(0, rule)

            handler = custom_router.find_handler(request, **kwargs)
            if handler is not None:
                return self.app.get_handler_delegate(request, handler, path_args=[request.path])

            # Forward other requests to the original handler
            return original_find_handler(self, request, **kwargs)

    class TornadoHook:
        def __init__(self, original_find_handler):
            self._original_find_handler = original_find_handler
            self._hooked = False

        def hook_tornado(self):
            if self._hooked:
                return
            # Inject our custom handler
            tornado.web.Application.find_handler = CustomApplication.find_handler
            self._hooked = True

        def unhook_tornado(self):
            if not self._hooked:
                return
            tornado.web.Application.find_handler = self._original_find_handler

            # Undo the injected rules
            for hooked_application in hooked_applications:
                if isinstance(hooked_application, Application):
                    # Unhook the application
                    for rule in injected_rule_list:
                        if rule in hooked_application.default_router.rules:
                            hooked_application.default_router.rules.remove(rule)

            # Clear the list of hooked applications
            hooked_applications.clear()
            self._hooked = False

    # Inject our custom handler
    tornado_hook = TornadoHook(original_find_handler)

    # Set the global hook
    with _global_hook_lock:
        if _global_tornado_hook:
            return False
        _global_tornado_hook = tornado_hook

    tornado_hook.hook_tornado()
    return True
    
def uninitialize_global_tornado_hook():
    """
    Uninitialize the global Tornado hook.

    This can be useful if you need to change the rules that are injected into the Streamlit application.'

    Returns:
        TRUE if the hooking mechanism was executed successfully, FALSE otherwise.
    """
    global _global_tornado_hook

    with _global_hook_lock:
        if _global_tornado_hook:
            _global_tornado_hook.unhook_tornado()
            _global_tornado_hook = None
            return True
    return False

def has_global_tornado_hook():
    """
    Returns:
        TRUE if the global Tornado hook is active, FALSE otherwise.
    """
    global _global_tornado_hook
    with _global_hook_lock:
        return _global_tornado_hook is not None