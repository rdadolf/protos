# Configuration File Options

----

### Section: `project`
Projects are a collection of related files to be scripted and controlled by a set of protos scripts.

`project-type` 
> **values:** `files` `git` `svn`<br>
> **default:** `'files'`<br>
> Describes how the project is stored. If the type is `'git'` or `'svn'`, the project will be cloned or checked out if it doesn't already exist.

`project-root'`
> **values:** absolute path<br>
> **default:** `''`<br>
> The project root directory. Must be an absolute path.

`protocol-path`
> **values:** `:`-separated absolute or relative path prefix strings<br>
> **default:** `''` <br>
> Searched left-to-right. Relative paths are relative to `project-root`. Empty paths between `:`'s or at the beginning or end signify the project directory.

`git-repo`
> **values:** git repository location<br>
> **default:** `''`<br>
> If `project-type` is `git`, the location for the project's git repository. If `project-type` is anything else, the option is ignored. Should be something that git understands, which includes usernames embedded in ssh URLs and absolute pathnames. Relative pathnames are not a good idea.

### Section: `log`

Logs are a complete record of experimental results, archived somewhere permanent.

`log-type`
> **values:** `files` `git` `svn`<br>
> **default:** `files`
> Describes how the log is stored. If the type is `git` or `svn`, the project will be cloned or checked out if it doesn't already exist.

`git-repo`
> **values:** git repository location<br>
> **default:** `''`<br>
> If `log-type` is `git`, the location for the log's git repository. If `log-type` is anything else, the option is ignored. Should be something that git understands, which includes usernames embedded in ssh URLs and absolute pathnames. Relative pathnames are not a good idea.

