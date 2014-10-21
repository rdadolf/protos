### User-level restrictions
Don't use *really* odd module invocations. Like:

    from protos import *
    require('pre-req') # OK
    
    import protos as prts
    prts.require('pre-req') # OK
    
    from protos import require as need
    need('pre-req') # OK
    
    from protos import require
    proxy = require
    proxy('pre-req') # Will not get detected

Be careful about using different config files across different machines. Certain directories and repositories *must* be identical across protocols. In order to keep the semi-independent nature of protocols, each must not rely on the implementation of the others. (If I change requirements in one, it shouldn't affect any another.) This means that we can't rely on a single configuration declaration from one protocol for a whole workflow---if we did, it could break if we removed or changed that one protocol. Instead, we're forced to check for consistency across protocols.
