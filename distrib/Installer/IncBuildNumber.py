i = file('BuildNumber.txt')
buildNumber = int(i.read().strip())
i.close()
buildNumber += 1
o = file('BuildNumber.txt','w')
print>>o, buildNumber
o.close()
