# SlimApp

The Slim Application Framework (SlimApp) is an all-in-one framework aiming to make development of PHP project, either web or console, faster and easier.

### Installation & Setup

The framework includes a list of useful PHP components. This makes it easy when setting up a new project: you would only need to use composer to require the project itself, and then run the project setup command.

Run the following command under a new project root directory to install the project:

```bash
composer require oasis/slimapp
```

After installation, you may initialize your project by running:

```bash
./vendor/bin/slimapp slimapp:project:init
```

Follow on screen prompts to provide necessary information, and your project directory structure will be automatically created.

Below is a list of explanations about asked info:

Name            | Explanation
---             | ---
_vendor_          | owner of this project, all lowercase alphabets/numbers, connected by hyphen '-'
_project_         | name of the project, all lowercase alphabets/numbers, connected by hyphen '-'
_root namespace_  | root namespace for all project specific classes
_source directory_ | as the name implies, source code directory, except unit testing source code and configuration files
_database support_ | Doctrine ORM support integration
_logging directory_ | directory to store logs (slimapp supports auto-configured file logging)
_data directory_  | directory where you store project data to local filesystem
_cache directory_ | directory to store cache files for configuration, container, routing and templates
_template directory_ | base directory to search for Twig template files

In the rest part of this document, we assume the project is called _test-project_ and the vendor is _minhao_. All other settings will retain their default values.

### Directory structure

An automatically initialized project will have a directory structure like below:

```
+ PROJECT_DIR/
    + assets/                            # static assets directory
    + bin/                               # executable directory
        - test-project.php             # auto-generated project CLI entry point (executable)
    + cache/                             # default cache directory
    + config/                            # config file direcotry
        - cli-config.php                 # auto-generated Doctrine CLI config file
        - config.yml                     # auto-generated configuration YAML file
        - routes.yml                     # auto-generated routing YAML file
        - services.yml                   # auto-generated service container (to be parsed by symfony/di)
    + src/                               # default source code (class files) directory
        + Controllers/                   # namespace for controller classes
            - DemoController.php         # as the name tells, a demo controller
        + Database/                      # namespace for db classes
            - TestProjectDatabase.php  # class which provides access to EntityManager and DBAL connection
        - TestProject.php              # base class for the project, extending SlimApp class
        - TestProjectConfiguration.php # configuration definition class for config/config.yml
    + templates/                         # default Twig template base directory
    + vendor/                            # composer components directory
    + web/                               # web entry directory
        - front.php                      # entry file for HTTP Kernel
    - bootstrap.php                      # bootstrap file
    - composer.json                      # composer config file
    - composer.lock                      # composer lock file
```

### Configuration

The fundamental configuration file for SlimApp is `config.yml` and it is located under the `config` directory. This is a YAML file which can be interpreted as an array in PHP. Below is the default content of an auto-generated config file:

```yaml
# config.yml

is_debug: true                          # is application in debug mode
dir:                                    # directory settings
    log: /data/logs/test-project        # logging dir
    data: /data/test-project            # data dir
    cache: /project-root/cache          # cache dir
    template: /project-root/templates   # template dir
db:                                     # database settings
    host: localhost                     # db host
    port: 3306                          # db port
    user: test_project                  # db user
    password: test-project              # db user password
    dbname: test_project                # db name
memcached:                              # cache settings
    host: localhost                     # memcached host
    port: 11211                         # memcached port
```

The `config.yml` file is strictly parsed, which means that all values defined in this file should meet a configuration definition. SlimApp utilizes [symfony/config] to support configuration definition and parsing of the configuration file. There is an auto-generated config definition class under `src/` directory.

### Bootstrap

To begin with using a SlimApp enabled app, let's first have a look at the `bootstrap.php` file, under **PROJECT_DIR**:

```php
<?php

use Minhao\TestProject\TestProject;
use Minhao\TestProject\TestProjectConfiguration;

require_once __DIR__ . "/vendor/autoload.php";

define('PROJECT_DIR', __DIR__);

/** @var TestProject $app */
$app = TestProject::app();
$app->init(__DIR__ . "/config", new TestProjectConfiguration(), __DIR__ . "/cache/config");

return $app;

```

There are a few things to be noticed:

- composer component autoloading is done in this file
- the configuration definition is instantiated on-the-fly, using the auto-generated config definition class `TestProjectConfiguration`
- the bootstrap file returns an object of type `TestProject`, which is an extension of `SlimApp`

### Refer to Config Value

With an instance of `TestProject` (hence an instance of `SlimApp`), we can access the config value in two slightly different ways:

##### get value by config key:

```php
<?php

use Oasis\SlimApp\SlimApp;
use Oasis\Mlib\Utils\DataProviderInterface;

/** @var SlimApp $app */
$isDebug           = $app->getMandatoryConfig('is_debug', DataProviderInterface::BOOL_TYPE);
$logDir            = $app->getMandatoryConfig('dir.log', DataProviderInterface::STRING_TYPE);
$nonExistingConfig = $app->getMandatoryConfig('non_existing_config'); // will throw
$port              = $app->getOptionalConfig('db.port', DataProviderInterface::INT_TYPE, 3306);
$nonExistingConfig = $app->getOptionalConfig('non_existing_config'); // will return null

```

**NOTE**: hierarchical config keys can be concatenated by a dot "."

##### get value by common parameter key:

```php
<?php

use Oasis\SlimApp\SlimApp;
use Oasis\Mlib\Utils\DataProviderInterface;

/** @var SlimApp $app */
$isDebug           = $app->getParameter('app.is_debug');
$dbPort            = $app->getParameter('app.db.port');
$nonExistingConfig = $app->getParameter('app.non_existing_config'); // will throw

```

Compared to the first method, the _parameter key_ only prepends a "app." prefix to the _config key_. And furthermore, all parameter keys are required to exist, or an exception will be thrown when accessed.

In practice, we suggest using the parameter key because it is consistent with how you access parameter in container definitions and twig templates. On the other side, the auto type checking ability when using _config key_ is an useful advantage some times.

### Service Container

SlimApp makes use of [dependency injection design pattern](https://en.wikipedia.org/wiki/Dependency_injection) heavily. Internally, it uses the [symfony/dependency-injection] component to implement a service container.

There is a centralized service container definition file, in the format of YAML, located under the `config` directory. This file is named: `services.yml`, and a sample can be found below:

```yaml
# services.yml
imports:
    - { resource: "external_definition1.yml" }
    - { resource: "external_definition2.yml" }

parameters:
    default.namespace:
        - Oasis\Mlib\
        - Minhao\TestProject\

services:
    app:
        properties:
            logging:
                path: '%app.dir.log%'
                level: debug
            cli:
                name: test-project
                version: '0.1'
            http:
                cache_dir: '%app.dir.cache%'
                routing:
                    path: '%app.dir.config%/routes.yml'
                    namespaces:
                        - Minhao\TestProject\
                        - Minhao\TestProject\Controllers\
                twig:
                    template_dir: '%app.dir.template%'
                    globals:
                        app: '@app'
                injected_args:
                    - '@entity_manager'
    memcached:
        class: Memcached
        calls:
            -
                - addServer
                -
                    - '%app.memcached.host%'
                    - '%app.memcached.port%'
    entity_manager:
        class: Doctrine\ORM\EntityManager
        factory:
            - Minhao\TestProject\Database\TestProjectDatabase
            - getEntityManager
```

A common `services.yml` file consists of three parts:

- **imports**: this is where you import other service definition files. With the help of imports, we can break large service definition files into smaller and more meaningful pieces.
- **parameters**: this is an array of parameters in key-value pairs. All parameters defined here, together with those defined in the `config.yml` (accessed by using their coresponding _parameter key_), can be dereferenced using the "%%" notation, **e.g.** '%app.memcached.host%'
- **services**: this is the real definition of services. A service is a key referring to an injectable variable. Services can be refered in other services too, using the "@" notation, **e.g.** '%entity_manager'

### Service Description

The way how a service is defined deserves a more detailed explanation. The descriptions (allowed attributes under the service key) can be separated into 3 phases:

- the constructing phase
- the setting phase
- the decoration phase

##### The Construction Phase

First of all, any service needs to have a type, and this is described using the `class` attribute.

> **NOTE** the class name has to be fully qualified unless a prefix namespace can be found in parameter '%default.namespace%'

With the `class` defined, we will need to access the object. There are 2 ways to get a service object:
- by instantiating it using constructor
- or by using a factory class (or a factory object) to get the service

```yaml
services:
    object.constructed:
        class: Minhao\TestProject\User
        arguments:
            - "John Smith" # name
            - 25 # age
    object.factory.provided:
        class: Minhao\TestProject\User
        factory: [UserProvider, getUser] # factory class, factory method
        arguments:
            - 250008 # student ID
```

##### The Setting Phase

After a service object is defined, we can modify the object as well, this is done like the example below:

```yaml
services:
    object.modified:
        class: Minhao\TestProject\User
        arguments:
            - "John Smith" # name
            - 25 # age
        properties:
            tel: "1234567890" # accessed as public property
            age: 40 # accessed as public property, overrides constructor
        calls:
            - [setSupervisor, "@another.user"] # method and arguments
```

As you can see, we can further modify a service either by accessing its properties, or by calling methods on the object.

> **NOTE** same as constructing phase, all attributes defined in setting phase will only be applied once, right after constructing phase

##### The decoration phase:

There are more powerful techniques to describe a service. Although they are not popularly used in practice, you may still be interested in having a look at them. Follow the [guides](http://symfony.com/doc/current/components/dependency_injection/advanced.html "Advanced Container Configuration") on Symfony's official website to find out more.

### Define the "@app" service

There is one and only one special service that **MUST** be well described in the `services.yml`, and this is the "app" service.

The constructing phase of the "app" service is done automatically and needs little extra attention. It is the `properties` attributes that differentiates each application:

```yml
services:
    app:
        properties:
            logging:
                path: %app.dir.log%
                level: debug
                handlers: # array extra monolog hanlders
                    - "@log.handler.email"
            cli:
                name: Slim App Console
                version: 1.1
                commands: # array of command object
                    - '@cli.command.dummy'
            http: # http bootstrap config
```

### Logging

SlimApp uses [oasis/logging] as the logging tool. [oasis/logging] provides a plug-and-use [PSR-3] compatible logging solution, which is built on top of [monolog].

By default, SlimApp will install two log handlers:

- The local file log handler, which streams logs to local file system, based on the configured log level
- The local file error handler, which only saves logs to local file system when errors occur (i.e. an _error_ or higher level log is triggered)

And furthermore, for apps run on command line, an additional console log handler is installed. The console log handler will directly write to **STDERR** with [ANSI color](https://en.wikipedia.org/wiki/ANSI_escape_code#Colors) decoration enabled.

When defining the "@app" service, the `logging` property can be set with the following attributes:

attribute name          | explanation
---                     | ---
path                    | log path for default file logger (both normal one and error one)<br />**NOTE**: the logs will be grouped into dates directory automatically
level                   | [PSR-3] standard log level, case-insensitive string
handlers                | array of additional log handlers to install, use other defined services here

### HTTP Kernel

Remember we claimed that SlimApp is a micro framework for both web and console development? It is now time to learn how SlimApp offers us the ability to make web applications in an easy yet powerful fashion.

SlimApp uses [oasis/http] as its HTTP Kernel implementation. [oasis/http] is an extension to the widely used [Silex] framework, and provides a kernel definition strictly implementing the `Symfony\Component\HttpKernel\HttpKernelInterface`.

It is already well documented in [oasis/http] about how to bootstrap an HTTP Kernel. So what we are going to introduce here is much simpler, i.e. how to inject bootstrap configuration in our service definition:

There is a property for the "@app" service, `http`, which will be passed to [oasis/http] as bootstrap configuration. The value of `http` must be an array complying with the [oasis/http standard](https://github.com/oasmobile/php-http/#bootstrap-configuration). Below is a sample configuration:

```yaml
services:
    app:
        properties:
            http:
                routing:
                    path: %app.dir.config%/routes.yml
                    namespaces:
                        - Oasis\SlimApp\Ut\
                error_handlers: '@http.error_handler'
                view_handlers: '@http.view_handler'
                cors:
                    -
                        path:       /cors/*
                        origins:    "*"
```

When everthing is well configured, we can use the HTTP Kernel like how it is demonstrated in the auto-generated `front.php` file:

```php
<?php

use Minhao\TestProject\TestProject;

/** @var TestProject $app */
$app = require_once __DIR__ . "/../bootstrap.php";

$app->getHttpKernel()->run();

```

### Command Line Interface

As discuessed, SlimApp is not only meant for web applications. It also provides a rich featured CLI framework. The underlying implementation heavily uses the [symfony/console] component. Although it does not require a comprehensive knowledge about [symfony/console] to start using the basic CLI features of SlimApp, it is recommended to go through the symfony documentation if you would like to extend the framework or make use of some advanced features.

First, let us have a look at the `cli` property of the "@app" servie:

```yaml
ervices:
    app:
        properties:
            cli:
                name: Slim App Console
                version: 1.1
                commands: # array of command object
                    - '@cli.command.dummy'
```

There are 3 attributes which can be set:

- _name_: the name of the console app, which is used when information is asked (like --help)
- _version_: the version of the console app, used in pair with the _name_ attribute
- _commands_: an array of app specific commands. The command object must also be a defined service of the type `Symfony\Component\Console\Command\Command`.

The console app can be started from the auto-generated entry script at **PROJECT_DIR**/bin/<project-name>.php:

```bash
./bin/test-project.php <command>
```

There is a mandatory _command_ argument, which is used to determine which `Command` object to invoke. Everything after the _command_ argument will be interpreted as input arguments and options.

**NOTE**: it is also possible (and probably more convenient with the help of an IDE with auto-complete feature) to inject supported commands into the CLI by calling the `addCommands()` method in console entry script:

```php
<?php
use Minhao\TestProject\TestProject;

/** @var TestProject $app */
$app = require_once __DIR__ . "/../bootstrap.php";

$console = $app->getConsoleApplication();
$console->addCommands(
    [
        new MyCustomCommandOne(),
        new MyCustomCommandTwo(),
    ]
);

$console->run();

```

##### Writing Your Own Command

To create your own command, you can start by extending the `Symfony\Component\Console\Command\Command` class and override at least the `configure()` method and the `execute()` method:

```php
<?php

namespace Minhao\TestProject\Console\Commands;

use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\OutputInterface;

class MyCustomCommandOne extends Command
{
    protected function configure()
    {
        parent::configure();

        $this->setName('custom:command:one')
            ->setDescription("Say hello world!");
    }

    protected function execute(InputInterface $input, OutputInterface $output)
    {
        $output->writeln("Hello World!");
    }
}

```

> **NOTE**: the command is put into the namespace `Console\Commands\` under root namespace of the project. This is a convention of SlimApp and is advised to be followed.

##### Using Input Argument

A command without any arguments is useless in most practical scenarios. We can tell a command to accept input arguments.

> **NOTE**: it is worth noticing the difference between command line argument and command input argment. When we execute a command in shell, the shell separates the whole input line into _command line arguments_ delimited by space. When executing our CLI command, the first _command line argument_ ($arg[0]) is the entry script name, and the second ($arg[1]) must be the command name. After that, any additional _command line arguments_ that does not start with a hyphen ('-') is considered to be an _input arguemnt_ (except option values, which follows an input option that requires value).

To enable your command to accept input arguments, you can use the `addArgument()` method to declare the arguments you expect, and you can use the `getArgument()` method on `$input` passed to `execut()` to read the argument:

```php
<?php

// namespace imports omitted ...

class MyCustomCommandOne extends Command
{
    protected function configure()
    {
        parent::configure();

        $this->setName('custom:command:one')
             ->setDescription("Say hello world!");

        $this->addArgument(
            'name',
            InputArgument::REQUIRED,
            "give your name here"
        );
    }

    protected function execute(InputInterface $input, OutputInterface $output)
    {
        $name = $input->getArgument('name');
        $output->writeln('Hello, ' . $name . '!');
    }
}

```

Running the test command will output:

```bash
$ ./bin/test-project.php custom:command:one John
Hello, John!

```

> **NOTE**: you can expect more than one arguments. However, you can only declare _OPTIONAL_ arguments at the end of the list. To be more clear, there cannot be any _REQUIRED_ argument after an _OPTIONAL_ argument.

##### Using Input Option

Input options are command line arguments that start with one or two hyphen. As the name "opiton" suggests, input options are always optional. An input option name has two different forms: long option name and short option name. Long option name starts with two hyphens ("--") and is mandatory for every option. A short option starts with single hyphen ("-") and is optional.

In addition, there are certain input options which require values attached to them. These option values are set in two ways:

- direct command line argument following the option:

```bash
$ ./bin/test-project.php custom:command:one John -m question
```

- using an equal sign after the long option name:

```bash
$ ./bin/test-project.php custom:command:one John --mood=question
```

To declare and use input options, read the example code below:

```php
<?php

// namespace imports omitted ...

class MyCustomCommandOne extends Command
{
    protected function configure()
    {
        parent::configure();

        $this->setName('custom:command:one')
             ->setDescription("Say hello world!");

        $this->addArgument(
            'name',
            InputArgument::REQUIRED,
            "give your name here"
        );

        $this->addOption(
            'mood',
            'm',
            InputOption::VALUE_REQUIRED
        );
    }

    protected function execute(InputInterface $input, OutputInterface $output)
    {
        $name = $input->getArgument('name');
        $mood = $input->getOption('mood');
        $sign = ($mood == "question") ? "?" : "!";
        $output->writeln('Hello, ' . $name . '!');
    }
}

```

Executing the command will output like below:
```bash
$ ./bin/test-project.php custom:command:one John --mood=question
Hello, John?

```

### The Daemon Sentinel

In practice, a project can have a number of commands to be executed in a pre-determined schedule. Some of the commands need to be executed at a given interval, some need to run more than one instance in parallel, some need to automatically send alert when execution fails, and so on. SlimApp provides a very useful feature called the Daemon Sentinel just to solve this problem.

A Daemon Sentinel itself is also a **command**. Your application should extend the `Oasis\SlimApp\SentinelCommand\AbstractDaemonSentinelCommand` to have your command class:

```php
<?php

namespace Minhao\TestProject\Console\Commands;

use Oasis\SlimApp\SentinelCommand\AbstractDaemonSentinelCommand;

class TestSentinelCommand extends AbstractDaemonSentinelCommand
{
    protected function configure()
    {
        parent::configure();
        $this->setName('test:daemon');
    }
}

```

When executed, the command expects a configuration file as its first argument. The format of the file should be YAML, and a sample is like below:

```yaml
commands:
    
    dummy: # name of the daemon, informative only, use any name meaningful

        # command name
        name: dummy:job

        # command line arguments to pass to the command
        args:
            a: moking
            --tt: true
            -vvv:

        # whether to run in parallel, and if yes, how many
        parallel: 3

        # run only once? if not, command will restart upon previous execution ends
        once: false

        # alert on abnormal exit (exit != 0)
        alert: false

        # interval: num of seconds between last end and next start
        interval: 2

        # frequency: min seconds between two start
        frequency: 5
```

[symfony/config]: http://symfony.com/doc/master//components/config/index.html
[symfony/dependency-injection]: http://symfony.com/doc/master/components/dependency_injection/index.html
[symfony/console]: http://symfony.com/doc/current/components/console.html
[oasis/http]: https://github.com/oasmobile/php-http/ "Oasis HTTP Kernel Component"
[oasis/logging]: https://github.com/oasmobile/php-logging/ "Oasis Logging Component"
[Silex]: http://silex.sensiolabs.org/
[monolog]: https://github.com/Seldaek/monolog
[PSR-3]: www.php-fig.org/psr/psr-3/ "PHP Standard Recommendation for Logging Interface"
