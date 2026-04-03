---
title: 【进阶】RecyclerView源码解析(三)——深度解析缓存机制
date: 2018-04-17 21:12:20+08:00
categories: ["Android源码分析"]
source_name: "【进阶】RecyclerView源码解析(三)——深度解析缓存机制"
jianshu_views: 12490
jianshu_url: "https://www.jianshu.com/p/2b19e9bcda84"
---
>本系列博客基于`com.android.support:recyclerview-v7:26.1.0`
>1.[【进阶】RecyclerView源码解析(一)——绘制流程](https://www.jianshu.com/p/c52b947fe064)
>2.[【进阶】RecyclerView源码解析(二)——缓存机制](https://www.jianshu.com/p/e44961f8add5)
>3.[【进阶】RecyclerView源码解析(三)——深度解析缓存机制](https://www.jianshu.com/p/2b19e9bcda84)
>4.[【进阶】RecyclerView源码解析(四)——RecyclerView进阶优化使用](https://www.jianshu.com/p/52791ac320f6)
>5.[【框架】基于AOP的RecyclerView复杂楼层样式的开发框架，楼层打通，支持组件化，支持MVP(不用每次再写Adapter了～)](https://www.jianshu.com/p/f45e4bcb8d92)

上一篇博客从源码角度分析了RecyclerView读取缓存的步骤，让我们对于RecyclerView的缓存有了一个初步的理解，但对于RecyclerView的缓存的原理还是不能理解。本篇博客将从实际项目角度来理解RecyclerView的缓存原理。
项目的截图如下：![Demo](/assets/img/posts/a593ea3256419fb6.png)

其中可以看到，这里是一个我们经常使用RecycleView实现列表。右侧输出面板展示了ScrapView的最大数量，CacheView的数量和内容，Pool中存在的内容。左侧面板展示了onBindViewHolder和onCreateViewHolder的过程。(Demo是基于一篇博客的Demo的拓展:[手摸手第二弹，可视化 RecyclerView 缓存机制](https://juejin.im/post/5a5d3d9b518825734216e1e8))
Demo地址：[RecyclerViewStudy](https://github.com/DrownCoder/RecyclerViewStudy)感兴趣的可以顺手点个star~
### 1.ScrapViews
>起初，我对于这个缓存的概念一直很模糊，我尝试过很多方法想要将这个缓存中的View读取出来看看里面的内容，但是发现这个缓存的大小总是为0，这个就让我很疑惑一个大
>小总是为0的缓存还有什么作用？
无意中读到了一篇[博客](https://blog.csdn.net/fyfcauc/article/details/54342303)，这篇博客对于RecyclerView提出了Detach和Remove的概念的区别，对于RecycleView的ScrapView进行了讲解。
#### 1.1 Detach和Remove
所以我们需要区分两个概念，**Detach**和**Remove**
>**detach**: 在ViewGroup中的实现很简单，只是将ChildView从ParentView的ChildView数组中移除，ChildView的mParent设置为null, 可以理解为轻量级的临时remove, 因
>为View此时和View树还是藕断丝连, 这个函数被经常用来改变ChildView在ChildView数组中的次序。View被detach一般是临时的，在后面会被重新attach。
>**remove**: 真正的移除，不光被从ChildView数组中除名，其他和View树各项联系也会被彻底斩断(不考虑Animation/LayoutTransition这种特殊情况)， 比如焦点被清除，从TouchTarget中被移除等。
#### 1.2 缓存作用
首先我们要了解，任何一个ViewGroup都会经历两次onLayout的过程，对应的childView就会经历detach和attach的过程，而在这个过程中，ScrapViews就起了缓存的作用，这样就不需要重复创建childView和bind。
**所以ScrapView主要用于对于屏幕内的ChildView的缓存，缓存中的ViewHolder不需要重新Bind，缓存时机是在onLayout的过程中，并且用完即清空**
#### 1.3 Demo验证
我们可以看一下demo验证一下我们的想法。
首先我们重写了RecylclerView的onLayout方法。
```
@Override
    protected void onLayout(boolean changed, int l, int t, int r, int b) {
        onLayoutListener.beforeLayout();
        super.onLayout(changed, l, t, r, b);
        onLayoutListener.afterLayout();
    }
```
在beforLayout时设置通过**反射**将RecyclerView内部的**mAttachedScrap**替换成我们自己重写的数据结构。
```
public void setAllCache() {
        try {
            Field mRecycler =
                    Class.forName("android.support.v7.widget.RecyclerView").getDeclaredField("mRecycler");
            mRecycler.setAccessible(true);
            RecyclerView.Recycler recyclerInstance =
                    (RecyclerView.Recycler) mRecycler.get(this);

            Class<?> recyclerClass = Class.forName(mRecycler.getType().getName());
            Field mAttachedScrap = recyclerClass.getDeclaredField("mAttachedScrap");
            mAttachedScrap.setAccessible(true);
            mAttachedScrap.set(recyclerInstance, mAttachedRecord);
            Field mCacheViews = recyclerClass.getDeclaredField("mCachedViews");
            mCacheViews.setAccessible(true);
            mCacheViews.set(recyclerInstance, mCachedRecord);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
```
为什么要这样做哪？这里利用了[Hook](https://www.jianshu.com/p/4f6d20076922)的思想。这样的话，RecyclerView内部在对**mAttachedScrap**进行操作的时候，比如RecyclerView内部对于**mAttachedScrap**的添加是使用add(T t)这个方法，这样我们设置的子类只要重写这个add(T t)的方法，在添加的时候就会调用我们子类重写的add方法。
```
    @Override
    public boolean add(T t) {
        RecyclerView.ViewHolder vh = (RecyclerView.ViewHolder) t;
        RcyLog.log(key + "添加---【position=" + vh.getAdapterPosition() + "】");
        if (canReset) {
            if (size() + 1 > lastSize) {
                maxSize = size() + 1;
            }
        }
        return super.add(t);
    }

    @Override
    public T remove(int index) {
        RecyclerView.ViewHolder vh = (RecyclerView.ViewHolder) get(index);
        RcyLog.log(key + "移除---【position=" + vh.getAdapterPosition() + "】");
        return super.remove(index);
    }

```
可以看到这里，当RecyclerView内部对**mAttachedScrap**进行add和remove的时候，我们都会进行打印log。并且记录一下maxSize。按照我们的猜想，RecyclerView会在onLayout的过程中对**mAttachedScrap**进行添加和移除操作，执行完后，**mAttachedScrap**的大小为0。
![第一次进入应用](/assets/img/posts/4d9abec14226b95f.png)
![Log截图](/assets/img/posts/5d595a7d38086059.png)
可以看到我们打开应用Demo的这个操作，没有做其他任何操作，仅仅是打开，**mAttachedScrap**经历了添加屏幕内9个ChildView的过程，并将9个ChildView移除的过程。而**mAttachedScrap**的大小刚好为屏幕内可以显示的Item的数量。
为什么说不需要重写Bind哪？通过上篇[博客](https://www.jianshu.com/p/e44961f8add5)，我们从源码角度对RecyclerView的缓存有了一个初步的了解：
```
//先从scrap中寻找
        for (int i = 0; i < scrapCount; i++) {
            final ViewHolder holder = mAttachedScrap.get(i);
            if (!holder.wasReturnedFromScrap() && holder.getLayoutPosition() == position
                    && !holder.isInvalid() && (mState.mInPreLayout || !holder.isRemoved())) {
                holder.addFlags(ViewHolder.FLAG_RETURNED_FROM_SCRAP);
                return holder;
            }
        }
        
        
         boolean bound = false;
        if (mState.isPreLayout() && holder.isBound()) {
            // do not update unless we absolutely have to.
            holder.mPreLayoutPosition = position;
        } else if (!holder.isBound() || holder.needsUpdate() || holder.isInvalid()) {
            //如果FLAG是ViewHolder.FLAG_UPDATE | ViewHolder.FLAG_INVALID,则需要调bind
            if (DEBUG && holder.isRemoved()) {
                throw new IllegalStateException("Removed holder should be bound and it should"
                        + " come here only in pre-layout. Holder: " + holder
                        + exceptionLabel());
            }
            final int offsetPosition = mAdapterHelper.findPositionOffset(position);
            bound = tryBindViewHolderByDeadline(holder, offsetPosition, position, deadlineNs);
        }
```
可以看到，我们在Scrap中寻找的时候，是有一个判断```!holder.isInvalid() ```，而对于需要bind的时候判断是否需要bind有一个判断``` holder.isInvalid()```。所以两个条件是互斥的。
### 2.CacheViews
 CacheViews其实就是和我们平常使用过程中息息相关的一个缓存。CacheViews缓存的特点是CacheViews内的缓存在复用的时候不需要调用bind，也就是在滑动的过程中，免去了bind的过程，提高滑动的效率。
 #### 2.1 缓存源码
 首先来看一下对于CacheViews内缓存的获取的源码：
 ```
 / /Search in our first-level recycled view cache.
            final int cacheSize = mCachedViews.size();
            for (int i = 0; i < cacheSize; i++) {
                final ViewHolder holder = mCachedViews.get(i);
                // invalid view holders may be in cache if adapter has stable ids as they can be
                // retrieved via getScrapOrCachedViewForId
                if (!holder.isInvalid() && holder.getLayoutPosition() == position) {
                    if (!dryRun) {
                        mCachedViews.remove(i);
                    }
                    if (DEBUG) {
                        Log.d(TAG, "getScrapOrHiddenOrCachedHolderForPosition(" + position
                                + ") found match in cache: " + holder);
                    }
                    return holder;
                }
            }
 ```
 首先我们通过源码可以知道CacheViews是一个ArrayList，可以看到获取的时候是遍历CacheViews，当缓存的ViewHolder和所需要的position相同的并且有效才可以复用。
 和上面分析的一样，可以知道这个缓存的ViewHolder是有效的才可以复用，所以在判断是否需要bind的时候，就不需要重新bind了。
 接着来看一下缓存的源码：
 既然是缓存，那肯定是滑动过程中的比较直观：
 ```
 @Override
    public boolean onTouchEvent(MotionEvent e) {
            case MotionEvent.ACTION_MOVE: {
		.........
                    if (scrollByInternal(
                            canScrollHorizontally ? dx : 0,
                            canScrollVertically ? dy : 0,
                            vtev)) {
                        getParent().requestDisallowInterceptTouchEvent(true);
                    }
               ........
        return true;
    }
    
    
    boolean scrollByInternal(int x, int y, MotionEvent ev) {
        ......
            if (x != 0) {
                consumedX = mLayout.scrollHorizontallyBy(x, mRecycler, mState);
                unconsumedX = x - consumedX;
            }
            if (y != 0) {
                consumedY = mLayout.scrollVerticallyBy(y, mRecycler, mState);
                unconsumedY = y - consumedY;
            }
           .......
        return consumedX != 0 || consumedY != 0;
    }
 ```
 可以看到这里省略了部分代码，在```onTouchEvent```的ACTION_MOVE事件中，可以看到，这里对```canScrollVertically```方法进行了判断，并最终将偏移量传给了```scrollByInternal```方法，而在```scrollByInternal```方法中，调用了LayoutManager的```scrollVerticallyBy```方法。而```scrollVerticallyBy```最后调用了```scrollBy```方法。
 ```
 int scrollBy(int dy, RecyclerView.Recycler recycler, RecyclerView.State state) {
        ......
        //调用了fill方法
        final int consumed = mLayoutState.mScrollingOffset
                + fill(recycler, mLayoutState, state, false);
       	......
        return scrolled;
    }
 ```
可以看到fill方法又调回了前一篇博客分析的**fill()**方法，这样就很明显了。而缓存的源码其实上面博客上面提到过一个方法```onLayoutChild()```方法里面有个```detachAndScrapAttachedViews```方法。
```
public void detachAndScrapAttachedViews(Recycler recycler) {
        final int childCount = getChildCount();
        for (int i = childCount - 1; i >= 0; i--) {
            final View v = getChildAt(i);
            scrapOrRecycleView(recycler, i, v);
        }
    }
    
    /**
     * 1.Recycle操作对应的是removeView, View被remove后调用Recycler的recycleViewHolderInternal回收其ViewHolder
     2.Scrap操作对应的是detachView，View被detach后调用Reccyler的scrapView暂存其ViewHolder
     * @param recycler
     * @param index
     * @param view
     */
    private void scrapOrRecycleView(Recycler recycler, int index, View view) {
        final ViewHolder viewHolder = getChildViewHolderInt(view);
        if (viewHolder.shouldIgnore()) {
            if (DEBUG) {
                Log.d(TAG, "ignoring view " + viewHolder);
            }
            return;
        }
        if (viewHolder.isInvalid() && !viewHolder.isRemoved()
                && !mRecyclerView.mAdapter.hasStableIds()) {
            //注意这里是remove
            removeViewAt(index);
            //往cacheview和pool中
            recycler.recycleViewHolderInternal(viewHolder);
        } else {
            //注意这里是detach
            detachViewAt(index);
            //存到scrap中
            recycler.scrapView(view);
            mRecyclerView.mViewInfoStore.onViewDetached(viewHolder);
        }
    }
```
这里就可以看到前面所说的**Remove和Detach的区别**，如果是remove，会执行```recycleViewHolderInternal(viewHolder);```方法，而这个方法最终会将ViewHolder加入CacheView和Pool中，而当是Detach，会将View加入到ScrapViews中，注意**View和ViewHolder的区别**，前面提到过，ScrapViews是对View的复用，而CacheView和Pool是对ViewHolder的复用。
既然是看CacheViews，那么就看一下```recycleViewHolderInternal```方法。
```
void recycleViewHolderInternal(ViewHolder holder) {
      	......
        if (forceRecycle || holder.isRecyclable()) {
            if (mViewCacheMax > 0
                    && !holder.hasAnyOfTheFlags(ViewHolder.FLAG_INVALID
                    | ViewHolder.FLAG_REMOVED
                    | ViewHolder.FLAG_UPDATE
                    | ViewHolder.FLAG_ADAPTER_POSITION_UNKNOWN)) {
                // Retire oldest cached view
                int cachedViewSize = mCachedViews.size();
                //如果超过默认大小，则删除第一个
                if (cachedViewSize >= mViewCacheMax && cachedViewSize > 0) {
                //从CacheViews中删除第一个，并加入到Pool中
                    recycleCachedViewAt(0);
                    cachedViewSize--;
                }
		......
                //加入缓存
                mCachedViews.add(targetCacheIndex, holder);
                cached = true;
            }
            if (!cached) {
                //不然直接加入Pool中
                addViewHolderToRecycledViewPool(holder, true);
                recycled = true;
            }
		.......
    }
```
可以看到几个关键逻辑：

>1.如果超过默认大小，则会移除CacheViews中的第一个，并加入到Pool中，然后在将需要加入缓存的ViweHolder加入到CacheView中。
>2.如果不能加入到CacheViews中，则加入到Pool中。
#### 2.2 Demo验证
(1)**进入应用**
我们首先进入应用会发现当前CacheViews的大小是0，也就是说进入应用时没有滑动，是没有任何ViewHolder回收的，这不需要解释吧。。。，而且Bind也只走了页面渲染的0-8。
![进入应用](/assets/img/posts/dfa3fb15d9e5128c.png)
(2)**向下滑动一个，第一个移除**
这时我们向下滑动，加载出第9个
![滑动一个](/assets/img/posts/3283294565df9351.png)
可以看到这时候除了加载了页面的```position=9```，还提前加载出了```position=10```，执行了onBind，而这时，由于第一个移出界面，所以```position=0```也就被加入到了CacheViews中。
(3)**向上滑动，再显示第一个**
![回到顶部](/assets/img/posts/5130eaf73563cdfe.png)
这时候我们会发现几个特别的点：
>1.onBind的面板没有新的Log，说明新出来的```position=0```没有走onBind方法。
>2.CacheViews中由刚才保存的```position=0```和```position=10```，变成了```position=10```和```position=9```
由此可见：
**CacheViews中缓存的ViewHolder当被复用的时候是不会走Bind流程的**
### 3.RecycledViewPool
其实根据前一节的讲解，我们已经对RecycleView的缓存有了一个很具体的了解了，RecyclerPool其实是RecyclerView区分ListView的一个亮点。**利用这级缓存我们可以实现多个RecyclerView之间的ViewHolder的复用。（关于这一点的利用我准备在下一篇博客对RecycleView使用的技巧进行举例讲解）**
#### 3.1 缓存源码
首先我们看一下ReyclerPool的结构。
```
public static class RecycledViewPool {
    private static final int DEFAULT_MAX_SCRAP = 5;
    static class ScrapData {
        ArrayList<ViewHolder> mScrapHeap = new ArrayList<>();
        int mMaxScrap = DEFAULT_MAX_SCRAP;
        long mCreateRunningAverageNs = 0;
        long mBindRunningAverageNs = 0;
    }
    SparseArray<ScrapData> mScrap = new SparseArray<>();
    }
```
可以看到RecyclerPool内部其实是一个**SparseArray**，可想而知，key就是我们的ViewType，而Value是ArrayList<ViewHolder>。
我们来看一下RecyclerPool的put方法。
```
public void putRecycledView(ViewHolder scrap) {
        final int viewType = scrap.getItemViewType();
        final ArrayList<ViewHolder> scrapHeap = getScrapDataForType(viewType).mScrapHeap;
        if (mScrap.get(viewType).mMaxScrap <= scrapHeap.size()) {
            return;
        }
        if (DEBUG && scrapHeap.contains(scrap)) {
            throw new IllegalArgumentException("this scrap item already exists");
        }
        //重置ViewHolder
        scrap.resetInternal();
        scrapHeap.add(scrap);
    }
```
其中**resetInternal**方法值得我们注意。
```
void resetInternal() {
        mFlags = 0;
        mPosition = NO_POSITION;
        mOldPosition = NO_POSITION;
        mItemId = NO_ID;
        mPreLayoutPosition = NO_POSITION;
        mIsRecyclableCount = 0;
        mShadowedHolder = null;
        mShadowingHolder = null;
        clearPayload();
        mWasImportantForAccessibilityBeforeHidden = ViewCompat.IMPORTANT_FOR_ACCESSIBILITY_AUTO;
        mPendingAccessibilityState = PENDING_ACCESSIBILITY_STATE_NOT_SET;
        clearNestedRecyclerViewIfNotNested(this);
    }
```
可以看到所有被put进入RecyclerPool中的ViewHolder都会被重置，这也就意味着RecyclerPool中的ViewHolder再被复用的时候是需要重新Bind的。这一点就可以区分和CacheViews中缓存的区别。
### 总结
还是那篇[Bugly博客](https://segmentfault.com/a/1190000007331249)中的图片吧（都怪我太懒了。。。）
![缓存总结](/assets/img/posts/9c246973157fb91b.jpg)
看过上面的分析，这张图片就很好理解了。

### 最后
给大家分享几篇我认为不错的RecyclerView源码分析的博客吧，我的分析其中有些地方就是从这些博客中学习来的。
>1.[Bugly分析ListView和RecyclerView的区别的，建议深入了解后再看](https://segmentfault.com/a/1190000007331249)
>2.[CSDN的一个大神的分析，分了有6篇博客，值得一读](https://blog.csdn.net/fyfcauc/article/details/54342303)
>3.[一篇很好的RecyclerView的源码分析博客，适合深入阅读](https://blog.csdn.net/qq_23012315/article/details/50807224)
>4.[可视化RecyclerView缓存机制，也就是本篇博客Demo的参考](https://juejin.im/post/5a52b0e15188257345015ad3)
>5.[一篇将RecyclerView的缓存讲的通俗易懂的博客，源码不是比较深入，但是很好理解](https://juejin.im/post/5ab99e29f265da23870ed86d)
。。。还有一些就不上了，以上5篇是我认为很值得反复阅读学习的。

**下篇博客可能是RecyclerView分析系列的结尾篇了，可能从实际使用角度分析一些我所了解的RecyclerView的一些进阶知识**

##### 相关
>基于AOP的RecyclerView复杂楼层样式的开发框架，楼层打通，支持组件化，支持MVP(不用每次再写Adapter了～)-[EMvp](https://github.com/DrownCoder/EMvp)
>Star👏支持一下～
>欢迎提issues讨论～
