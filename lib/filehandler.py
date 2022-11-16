class BufferFileHandler:  
  def __init__(self, path: str, flag:str, buffer_size: int):
    self.path = path
    self.file = open(self.path, flag)
    self.buffer_size = buffer_size
  
  def get_content(self, i):
    self.file.seek(i * self.buffer_size)
    return self.file.read(self.buffer_size)
  
  def write(self, content):
    self.file.write(content)
  
  def __del__(self):
    self.file.close()
    
