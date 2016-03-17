<?php
/**
 * Created by PhpStorm.
 * User: minhao
 * Date: 2016-03-17
 * Time: 20:23
 */

namespace Oasis\SlimApp\Ut;

use Symfony\Component\HttpFoundation\Response;

class TestController
{
    public function homeAction()
    {
        return new Response("HOME PAGE!!!");
    }
    
}
