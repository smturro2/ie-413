class Node:
  # value : is the value on which the list is sorted on.
  # data : is any additional data carried with the node
  # next : holds the next node
  def __init__(self):
    self.value = None
    self.data = None
    self.next = None

class LinkedList:
  def __init__(self):
    self.head = None

  def addNode(self, value,data=None):
    curr = self.head
    if curr is None:
      n = Node()
      n.data = data
      n.value = value
      self.head = n
      return

    if curr.value > value:
      n = Node()
      n.value = value
      n.next = curr
      n.data = data
      self.head = n
      return

    while curr.next is not None:
      if curr.next.value > value:
        break
      curr = curr.next
    n = Node()
    n.data = data
    n.value = value
    n.next = curr.next
    curr.next = n
    return

  def __str__(self):
    value = []
    curr = self.head
    while curr is not None:
      value.append(curr.value)
      curr = curr.next
    return "[%s]" %(', '.join(str(i) for i in value))

  def __repr__(self):
    return self.__str__()

def main():
  ll = LinkedList()
  num = int(input("Enter a number: "))
  while num != -1:
    ll.addNode(num)
    num = int(input("Enter a number: "))
  c = ll.head
  while c is not None:
    print(c.value)
    c = c.next
