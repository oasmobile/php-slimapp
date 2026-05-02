<?php
declare(strict_types=1);

namespace Oasis\SlimApp\Tests\Integration\Fixtures;

use Symfony\Component\HttpFoundation\Response;

class TestController
{
    public function homeAction(): Response
    {
        return new Response("HOME PAGE!!!");
    }
}
