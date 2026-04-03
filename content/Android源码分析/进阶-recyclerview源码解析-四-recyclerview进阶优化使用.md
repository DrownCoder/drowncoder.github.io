---
title: "【进阶】RecyclerView源码解析(四)——RecyclerView进阶优化使用"
date: 2018-04-24 21:33:19+08:00
categories: ["Android源码分析"]
source_name: "【进阶】RecyclerView源码解析(四)——RecyclerView进阶优化使用"
jianshu_views: 9192
jianshu_url: "https://www.jianshu.com/p/52791ac320f6"
---
>本系列博客基于`com.android.support:recyclerview-v7:26.1.0`
>1.[【进阶】RecyclerView源码解析(一)——绘制流程](https://www.jianshu.com/p/c52b947fe064)
>2.[【进阶】RecyclerView源码解析(二)——缓存机制](https://www.jianshu.com/p/e44961f8add5)
>3.[【进阶】RecyclerView源码解析(三)——深度解析缓存机制](https://www.jianshu.com/p/2b19e9bcda84)
>4.[【进阶】RecyclerView源码解析(四)——RecyclerView进阶优化使用](https://www.jianshu.com/p/52791ac320f6)
>5.[【框架】基于AOP的RecyclerView复杂楼层样式的开发框架，楼层打通，支持组件化，支持MVP(不用每次再写Adapter了～)](https://www.jianshu.com/p/f45e4bcb8d92)

>上一篇博客比较深度的对RecyclerView的缓存机制进行了分析，分别对SrapViews、CacheViews、RecyclerPool这三级缓存进行多角度分析和实际对Demo验证。前三篇博客可以说都是从源码对角度对RecyclerView进行分析，分别对RecyclerView的绘制机制，缓存源码，缓存机制三个角度进行深度分析，虽然都是从源码角度进行分析，比较抽象，但是对于我们理解RecyclerView的使用有很大的帮助。
### 前言
本篇博客将打算从实际开发过程中，结合前面三篇博客的分析，总结一下RecyclerView的使用过程中的进阶使用（仅仅是我统计总结的，大家如果有其他的见解，欢迎大家在在评论区分享～）。

#### 一.不要在onBind的时候设置onClickListener
当为RecyclerView中的ItemView中的设置点击事件或者其他事件的时候，往往我们的写法总是在onBindViewHolder中给ItemView去设置点击事件。
```
@Override
    public void onBindViewHolder(ViewHolder holder, int position) {
        holder.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                //do something
            }
        });
    }
```
**问题**：这时候我们可以考虑一下我们这种写法是否合理，从前面的源码分析甚至对RecyclerView有一定基础了解的都知道```onBindViewHolder```的调用时机是View滑到页面可显示位置时，就会出发这个方法回调。那当我们这样设置的时候就意味着，这个View只要滑到屏幕内，这个我们就会给这个itemView设置一次onClickListener,并且这个onClickListener每次滑动的时候都是重新new出来的。显而易见这样是不合理的。好吧，那我们优化一下～  

**1.1 第一次优化**
```
@Override
    public void onBindViewHolder(ViewHolder holder, int position) {
        holder.setOnClickListener(mOnClickListener);
    }
    
    private View.OnClickListener mOnClickListener = new View.OnClickListener() {
        @Override
        public void onClick(View v) {
            //do something
        }
    }
```
**优化：** 嗯，这样看起来舒服多了，这样我们每次onBindViewHolder的时候设置的onClickListener都是同一个mOnClickListener,这样我们就不用每次在onBindViewHolder都new一个onClickListener了。  
**问题：** 
但是这样真 就够了吗？再回想一下，RecyclerView的优势就是对于ViewHolder的复用。这样考虑一下，当```position =1```的第一次显示在界面显示，我们已经对view设置过onClickListener，我们这是滑出```position=1```，再滑回```position=1```。当我们向下滑这时```position=1```被放入缓存，如果仅仅是在CacheViews缓存中还好，因为不会调onBindViewHolder方法（具体原因见[上篇博客](https://www.jianshu.com/p/2b19e9bcda84)）,如果是在CacheViews或者RecyclerPool的时候，每次滑入还会调onBindViewHolder方法，也就是说，**明明我们已经给这个View设置过onClickListener了，每次显示的时候，我们还要再给这个view设置一次onClickListener**，这样肯定是不合理的。那就再优化一下～  
**1.2 第二次优化**
```
private class XXXHolder extends RecyclerView.ViewHolder {
        private EditText mEt;
        EditHolder(View itemView) {
            super(itemView);
            mEt = (EditText) itemView;
            mEt.setOnClickListener(mOnClickListener);
        }
    }
    private View.OnClickListener mOnClickListener = new View.OnClickListener() {
        @Override
        public void onClick(View v) {
            //do something
        }
    }
```
没错，就是上面这样，既然每次Bind的时候没必要重复设置onClickListener,那么我们就在```onCreateViewHolder```中设置，在这个ViewHolder在new的时候，设置一个全局的OnClickListener。这样刚才考虑的问题就迎刃而解了。
#### 二.不要在onBindViewHolder做逻辑判断和计算。
这也是我们经常容易犯的问题，原因其实和第一条也是相似的，**每次滑入后我们都必须做完这些逻辑判断和计算，页面才能绘制出来**，这样明显是很消耗性能的。常见的一些逻辑判断：
>1.TextView.setText(Html.fromHtml(str);  
>2.计算UI的宽高比，margin，padding，每次都用DensityUtils.dp2px()转换。  
>3.每次都new一些可以复用都对象:adapter,viewparam  
>等。。。

**优化建议：**  
>1.可以考虑尽可能都逻辑前移  
>2.onBindViewHolderz中都对象考虑懒加载或者变成私有变量。

#### 三.RecyclerView嵌套RecyclerView考虑设置RecyclerPool缓存。
这个是我们经常考虑不到都一点，我们经常有这样都需求，一个竖向都RecyclerView需要展示多个横向滑动都RecyclerView都楼层。这时候我们就可以考虑使用RecyclerPool给子RecyclerView设置一个缓存池，这样当存在多个横向滑动的RecyclerView时，就可以减少子RecyclerView的子ViewHolder的创建，实现多个RecyclerView之间的复用。  
**代码实现：**
```
private RecyclerView.RecycledViewPool childPool;
public XXAdapter(){
    childPool = new RecyclerView.RecycledViewPool();
}
private class RcyViewHolder extends RecyclerView.ViewHolder {
        private SRecyclerView sRcy;

        public RcyViewHolder(View itemView) {
            super(itemView);
            sRcy = itemView.findViewById(R.id.rcy_child);
            LinearLayoutManager manager = new LinearLayoutManager(mContext);
            //1.设置回收
            manager.setRecycleChildrenOnDetach(true);
            manager.setOrientation(LinearLayoutManager.HORIZONTAL);
            sRcy.setLayoutManager(manager);
            //2.设置缓存Pool
            sRcy.setRecycledViewPool(childPool);
        }
    }
```
**Demo比较**  
Demo是上一篇[博客](https://www.jianshu.com/p/2b19e9bcda84)的拓展,一个父RecyclerView中包含两种类型的楼层，第一种是一个TextView,第二种是一个横向的RecyclerView。而子RecyclerView里面就是横向的多个ImageView的列表。  
>Demo地址：[RecyclerViewStudy](https://github.com/DrownCoder/RecyclerViewStudy)，感兴趣的可以star~  

首先我们来看一下没有设置RecyclerPool之前  
**3.1 没有设置RecyclerPool**  
![第一个ChildRecyclerView](/assets/img/posts/79280022fc1b6cc8.png)
可以看到，刚进入的时候，这时只有一个横向的ChildRecyclerView,从面板可以看到这时第一个ChildRecyclerView:new了三个ImageViewHolder。  
这时我们向下滑动展示出第二个横向的ChildRecyclerView。
![第二个ChildRecyclerView](/assets/img/posts/c16bf8816f9ae722.png)
可以看到，这时第二个横向的ChildRecyclerView滑入的时候，从面板可以看到，从刚才的new了三个的ImageViewHolder又new了三个ImageViewHolder。
**3.2 设置RecyclerPool**  
![第一个ChildRecyclerView](/assets/img/posts/d0f24238f9c813c5.png)
可以看到，这时候没有什么特殊的变化，由于只有一个横向的ChildRecyclerView，所以仍然只是new了三个ImageViewHolder。  
![第二个ChildRecyclerView](/assets/img/posts/2a071a0b110a0402.png)
这时候就可以清除的看到啊设置完RecyclerViewPool的变化了，可以发现第二个ChildRecyclerView滑入后，没有new任何新的ImageViewHolder，也就是说第二个ChildRecyclerView复用了第一个ChildRecyclerView的new出来的三个ImageViewHolder。**也就是说这时内存里只存在三个ImageViewHolder。**这样就节省了创建3个ImageViewHolder的时间。

#### 四.对于大量图片的RecyclerView考虑重写onScroll事件，滑动暂停后再加载
这个我们平时就经常实现了，当长图片列表的时候，我们经常做这样的优化，防止图片的大量加载，毕竟图片一直是内存占用大户。

#### 五.对于复杂布局的RecyclerView考虑重写onScroll事件，滑动暂停后再加载复杂布局
这个其实我们平时没有考虑，考虑一种情况：RecyclerView中存在几种绘制复杂，占用内存高的楼层类型，但是用户只是快速滑动到底部，并没有必要绘制计算这几种复杂类型，所以也可以考虑对滑动速度，滑动状态进行判断，满足条件后再加载这几种复杂的。

#### 六.不要什么都用notifydatasetchange!!!!
这个其实每个人都熟知，但是往往都不遵循，RecyclerView和ListView的一个显著区别就是RecyclerView提供了多种刷新类型，**不像ListView每次刷新都需要重新Bind界面内都所有都View。**RecyclerView通过给每个ViewHolder设置标志位来判断需要刷新的ViewHolder。具体原理如下图：(图片来源：多次提到的[Bugly博客](https://segmentfault.com/a/1190000007331249)～～)  
![RecyclerView刷新机制](/assets/img/posts/72e70774704690a9.png)
**6.1 Demo验证**
```
    case R.id.delete:
                mData.remove(0);
                //局部刷新
                //mAdapter.notifyItemRemoved(0);
                //全局刷新
                mAdapter.notifyDataSetChanged();
```
Demo很简单，就是点击删除后，移除第一个Item。  
![刚进入](/assets/img/posts/732206fed2414e4c.png)
![notifyDataSetChanged](/assets/img/posts/fb911c9ab92bc135.png)
可以看到，当我们仅仅是删除了第一项或者某一项，调用了```notifyDataSetChanged```方法，会导致整个页面范围内的ViewHolder重新调用onBindViewHolder方法，这样就重复做了一次Bind操作。这时我们换用```notifyItemRemoved```方法。
![notifyItemRemoved](/assets/img/posts/28a5ab4c7a89e7f1.png)
可以看到，这时只会由于第一个移除，导致新的一个`position=8`进入并展示，所以只有`position=8`调用了onBindViewHodler方法，而其他的已经绑定的ViewHolder不需要重新绑定。
#### 七.减少每个ItemView的层级嵌套
这就是老生常谈的优化了。
#### 八.升级Recycle版本到25以上的版本，使用recyclerview prefetch功能
关于Prefethc功能本篇博客就不讲解了，这里提供两篇博客供大家理解吧：
[RecyclerView Prefetch功能探究](https://blog.csdn.net/crazy_everyday_xrp/article/details/70344638)
[RecyclerView的新机制：预取（Prefetch）](https://juejin.im/entry/58a30bf461ff4b006b5b53e3)
#### 九.设置setItemViewCacheSize缓存大小
```
 recyclerView.setItemViewCacheSize(20);
 recyclerView.setDrawingCacheEnabled(true);
 recyclerView.setDrawingCacheQuality(View.DRAWING_CACHE_QUALITY_HIGH);
```
其实setItemViewCacheSize设置的是CacheViews的大小，通过前一篇[博客](https://www.jianshu.com/p/2b19e9bcda84)，我们应该知道CacheViews的特点：
>1.CacheViews中的缓存只能position相同才能复用，并且不会重新Bind.
>2.CacheViews满了后会移除到RecyclerPool中，并重置ViewHolder.
>3.RecyclerPool中的缓存复用需要重新Bind.

所以我们可以适当的通过调用setItemViewCacheSize方法，来增加CacheViews的大小（默认是2），来防止小范围的滑动导致的重复Bind而导致的卡顿。**典型的拿空间还时间，所以要考虑内存问题，根据自己的应用实际情况设置大小**
#### 十.如果RecyclerView固定宽高，只是用于展示固定大小的组件，然后设置```recyclerView.setHasFixedSize(true)```这样可以避免每次绘制Item时，不再重新计算Item高度。

### 总结
刚好凑够10条也算满足了强迫症的毛病～～～，以上仅仅是我个人的总结，如果大家还有什么不错的建议欢迎大家在下方**评论分享**。

>RecyclerView的源码系列到此算是结束了，四篇博客算是我收集的RecyclerView相关学习博客的总结和自己的分析。随着RecyclerView的使用场景越来越多，只有真正从源码角度理解了RecyclerView的绘制，缓存原理，才能进一步理解和优化我们通过RecycelrView实现的页面，真是应了那句话：**Read The Fucking Source Code**

##### 相关
>基于AOP的RecyclerView复杂楼层样式的开发框架，楼层打通，支持组件化，支持MVP(不用每次再写Adapter了～)-[EMvp](https://github.com/DrownCoder/EMvp)
>Star👏支持一下～
>欢迎提issues讨论～
