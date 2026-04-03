问题描述：
a. 行item图片显示重复
 这个显示重复是指当前行item显示了之前某行item的图片。
 比如ListView滑动到第2行会异步加载某个图片，但是加载很慢，加载过程中listView已经滑动到了第14行，且滑动过程中该图片加载结束，第2行已不在屏幕内，根据上面介绍的缓存原理，第2行的view可能被第14行复用，这样我们看到的就是第14行显示了本该属于第2行的图片，造成显示重复。
b. 行item图片显示错乱
 这个显示错乱是指某行item显示了不属于该行item的图片。
 比如ListView滑动到第2行会异步加载某个图片，但是加载很慢，加载过程中listView已经滑动到了第14行，第2行已不在屏幕内，根据上面介绍的缓存原理，第2行的view可能被第14行复用，第14行显示了第2行的View，这时之前的图片加载结束，就会显示在第14行，造成错乱。
c. 行item图片显示闪烁
 上面b的情况，第14行图片又很快加载结束，所以我们看到第14行先显示了第2行的图片，立马又显示了自己的图片进行覆盖造成闪烁错乱。
再来说说我的问题：
（1）和上述的一样listview用的异步加载图片后，图片闪烁并且图片显示会错位
（2）listview中 的每个item都有一个点赞效果，点击后拳头会变色，但是问题出来了，如下图一样，点击第一个后，拳头的确变红了，但是滑到第八个突然发现第八个也变红了！！！
[![](http://upload-images.jianshu.io/upload_images/7866586-0147cedb44368c0d?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)](http://photo.blog.sina.com.cn/showpic.html#blogid=&url=http://album.sina.com.cn/pic/004kijbAzy6XhB4dsQD27)

这是listview的缓存机制，
1.在getView()获取每行的Item并向下滑动的过程中，如果Item1已经完全滑出屏幕，且缓存中没有Item1对应的View，则将其put进缓存中。
2.将要滑入的Item8会先判断缓存中是否有可用的Item，如果有则直接将缓存中对应的View拿过来复用。 
3.ListView显示刚刚滑入的Item8,并将ListView中的各个Item都执行刷新(getView())操作
很同意看懂吧，在网上看了很多资料，也有很多分析，其中一位大神的分析，我记了下来，接下来是那个大神的分析：
listview 异步加载图片之所以错位的根本原因是重用了 convertView 且有异步操作.
如果不重用 convertView 不会出现错位现象， 重用 convertView 但没有异步操作也不会有问题。
我简单分析一下：
当重用 convertView 时，最初一屏显示 7 条记录， getView 被调用 7 次，创建了 7 个 convertView.
当 Item1 划出屏幕， Item8 进入屏幕时，这时没有为 Item8 创建新的 view 实例， Item8 复用的是
Item1 的 view 如果没有异步不会有任何问题，虽然 Item8 和 Item1 指向的是同一个 view，但滑到
Item8 时刷上了 Item8 的数据，这时 Item1 的数据和 Item8 是一样的，因为它们指向的是同一块内存，
但 Item1 已滚出了屏幕你看不见。当 Item1 再次可见时这块 view 又涮上了 Item1 的数据。
但当有异步下载时就有问题了,假设 Item1 的图片下载的比较慢，Item8 的图片下载的比较快，你滚上去
使 Item8 可见，这时 Item8 先显示它自己下载的图片没错，但等到 Item1 的图片也下载完时你发现
Item8 的图片也变成了 Item1 的图片，因为它们复用的是同一个 view。 如果 Item1 的图片下载的比
Item8 的图片快， Item1 先刷上自己下载的图片，这时你滑下去，Item8 的图片还没下载完， Item8
会先显示 Item1 的图片，因为它们是同一快内存，当 Item8 自己的图片下载完后 Item8 的图片又刷成
了自己的，你再滑上去使 Item1 可见， Item1 的图片也会和 Item8 的图片是一样的，
因为它们指向的是同一块内存。
所有解决方法来了：
（1），给 ImageView 设置一个 tag, 并预设一个图片。
当 Item1 比 Item8 图片下载的快时， 你滚下去使 Item8 可见，这时 ImageView 的 tag 被设成了
Item8 的 URL， 当 Item1 下载完时，由于 Item1 不可见现在的 tag 是 Item8 的 URL，所以不满足条件，
虽然下载下来了但不会设置到 ImageView 上, tag 标识的永远是可见 view 中图片的 URL。
（2）使用volley框架。。。放弃自己敲的代码 吧。。
我选择了第一种，下面是但的代码展示：
```// 给 ImageView 设置一个 
tagholder.post_dianzan.setTag(position);
// 预设一个图片
holder.post_dianzan.setBackgroundResource(R.drawable.praise1);
final ImageView dz = holder.post_dianzan;
final TextView dzl = holder.post_dianzanliang;
TextView content = holder.post_content;
holder.post_dianzan.setOnClickListener(new OnClickListener() {@Overridepublic void onClick(View v) {
        // TODO Auto-generated method stub
        //if(holder.post_dianzan.getTag().toString().equals(""+position))//{list.get(position).setIsDZ(true);
        list.get(position).setPost_dianzanliang("" + (Integer.parseInt(list.get(position).getPost_dianzanliang()) + 1));
        // 通过 tag 来防止图片错位if (v.getTag() != null && v.getTag().equals(position)) { ((ImageView) v).setBackgroundResource(R.drawable.praise2);
    }
    new Animation().praise(dz);
    String num = dzl.getText().toString();
    dzl.setText("" + (Integer.parseInt(num) + 1));
    Message message = new Message();
    Bundle bundle = new Bundle();
    bundle.putString("id", list.get(position).getPost_id());
    message.setData(bundle);
    //bundle传值，耗时，效率低
    handler.sendMessage(message);
    //发送message信息 
    message.what = 4;
    //
}
}
});
```

至此，问题解决了！！！！，黑体就是关键代码。
