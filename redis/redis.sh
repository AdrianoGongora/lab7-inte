redis-cli ping | grep PONG > /dev/null 2>&1

if [ $? != 0 ]; then
  echo "Redis is down"
  exit 1
else
  echo "Redis is up"
  exit 0
fi
