<?php

namespace Oasis\SlimApp\Tests\Integration\Fixtures;

use Symfony\Component\HttpFoundation\Response;

class TestController
{
    public function homeAction()
    {
        return new Response("HOME PAGE!!!");
    }
}
