#!/bin/bash

if [ ! -f "./o_rag_service" ];then
  ln -s \/root/miniconda3/bin/uwsgi ./o_rag_service
  else
  echo "o_rag_service已经存在"
fi
./o_rag_service --http :26666 --wsgi-file o_service.py --daemonize ./uwsgi_offical.log --master --processes 1 --threads 1 --lazy-apps &
ps -ef | grep o_rag_service 

