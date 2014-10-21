#!/bin/bash

for i in *.protocol
do
  echo $i
  ./$i -c long_chain.config
done
