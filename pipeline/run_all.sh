#!/bin/bash
cd /home/claude/out
for f in IMG_8406 IMG_8407 IMG_8408 IMG_8409 IMG_8410 IMG_8411 IMG_8412 IMG_8413 IMG_8414 IMG_8415 IMG_8416 IMG_8420 IMG_8421 IMG_8422 IMG_8423 IMG_8424 IMG_8425 IMG_8433; do
  [ -f $f.mp4 ] && continue
  python3 -I /home/claude/trials/pipeline/process.py /mnt/user-data/uploads/$f.mov /home/claude/out 2>&1 | grep -v Warning
  bash /home/claude/trials/pipeline/encode.sh /mnt/user-data/uploads/$f.mov $f.ass $f.tmp.mp4 && mv $f.tmp.mp4 $f.mp4 && echo "$f encoded"
done
echo ALL DONE
