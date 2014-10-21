# Protos Quick Start

----

#### Basics
*TODO*

#### Protocols
Protos is an embedded domain-specific language based on Python.
This is a fancy way of saying that protocols themselves are just python scripts with some special additions.
If you're familiar with automating your tasks with Python, then writing Protos protocols should be comfortable.
Let's try an example: compiling a program.

    # compile-hello.protocol
    import protos
    import os
    import subprocess as sub

    protos.config('hello.config')

    os.chdir('source-dir')
    sub.call('gcc -o hello hello.c')

    protos.log('source-dir/hello')
    protos.var('hello-program','source-dir/hello')

#### Creating a Workflow
Protos workflows are created implicitly by the dependencies you embed in your protocol scripts.
This means that as long as you always ensure that your protocols have the right prerequisites, you can just ask for the last protocol in the flow.
(Want to have multiple "last protocols"? Just make a new one with all of those as prerequisites and nothing else.)

To pick up with our running example, let's create a compile-execute workflow using the previous protocol. To do this, we just need to write an execute protocol that uses the compile one.

    # run-hello.protocol
    import protos
    import subprocess as sub

    protos.config('hello.config')

    protos.require('compile-hello')
    prog = protos.var('hello-program')
    out_file = 'hello-out'
    out_fd = open(out_file,'w')
    sub.call(prog, stdout=out_fd)

    protos.log(out_file)

#### Running a Workflow
The easiest way to run a Protos workflow is to just run the script.
The Protos framework will automatically take care of the rest.

    $ python run-hello.protocol

#### Backups
Good data stewardship mandates a disaster recovery plan. Backups are a good start, and they're relatively easy with Protos.
A single snapshot can be created a single command:

    ssh backup-machine git clone log-backups/

Recurring updates can be setup almost as easily:

    ssh backup-machine 'echo "@hourly git --work-tree=log-backups/ fetch" | crontab -e'
  

