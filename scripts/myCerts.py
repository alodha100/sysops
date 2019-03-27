import urllib.request

# "Gotta pump those numbers up" Mark Hanna 2013

count = 1000
for i in range(count):
    print(i)
    url = 'https://www.certmetrics.com/amazon/public/badge.aspx?i=2&t=c&d=2018-09-24&ci=AWS00371535'
    f = urllib.request.urlopen(url)
    # print(f.read())

print("Program just ran" , count, "times", sep=" ")