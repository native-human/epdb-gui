

def prefixfunction(pattern):
  P = ' ' + pattern 
  m = len(P) 
  pi = [None]*m
  pi[1] = 0
  k = 0
  for q in range(2,m):
    print(q, k)
    print("  ", k,(k+1,q), P[k+1], P[q])
    while k > 0 and P[k+1] != P[q]:
      print("    ", k,(k+1,q), P[k+1], P[q])
      k = pi[k]
    if P[k+1] == P[q]:
      k = k + 1
    pi[q] = k
  return pi

print(prefixfunction("ababbabbabbababbabb"))
