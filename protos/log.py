#!/usr/bin/env python3

import logging

class log:
  subordinate_logger = logging.Logger('protocol')

  @classmethod
  def debug(self,*strings):
    self.subordinate_logger.debug(''.join(map(str,strings)))
  @classmethod
  def warning(self,*strings):
    self.subordinate_logger.warning(''.join(map(str,strings)))
  @classmethod
  def error(self,*strings):
    self.subordinate_logger.error(''.join(map(str,strings)))
