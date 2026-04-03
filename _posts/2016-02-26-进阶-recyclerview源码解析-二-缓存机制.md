---
title: "【进阶】RecyclerView源码解析(二)——缓存机制"
date: 2018-04-02 21:00:48+08:00
categories: ["Android源码分析"]
source_name: "【进阶】RecyclerView源码解析(二)——缓存机制"
jianshu_views: 17688
jianshu_url: "https://www.jianshu.com/p/e44961f8add5"
---
>本系列博客基于`com.android.support:recyclerview-v7:26.1.0`
>1.[【进阶】RecyclerView源码解析(一)——绘制流程](https://www.jianshu.com/p/c52b947fe064)
>2.[【进阶】RecyclerView源码解析(二)——缓存机制](https://www.jianshu.com/p/e44961f8add5)
>3.[【进阶】RecyclerView源码解析(三)——深度解析缓存机制](https://www.jianshu.com/p/2b19e9bcda84)
>4.[【进阶】RecyclerView源码解析(四)——RecyclerView进阶优化使用](https://www.jianshu.com/p/52791ac320f6)
>5.[【框架】基于AOP的RecyclerView复杂楼层样式的开发框架，楼层打通，支持组件化，支持MVP(不用每次再写Adapter了～)](https://www.jianshu.com/p/f45e4bcb8d92)

>接着上一篇博客分析完RecyclerView的绘制流程，其实对RecyclerView已经有了一个大体的了解，尤其是RecyclerView和LayoutManager和ItemDecoration的关系。 本篇文章将对RecyclerView的缓存机制的讲解，但由于缓存对于RecyclerView非常重要，所以准备分几部分进行分析，本篇博客主要从源码角度进行分析缓存的流程。
### 前言
无论是原来使用的ListView还是RecyclerView，列表类型的视图一直是原生使用的一个重头戏。无论是从使用功能上还是性能上，原生的列表视图都有着巨大的优势，而这个优势很重要的一方面其实就是对于视图的复用机制，也就是**缓存**。从ListView的**RecycleBin**到RecyclerView的**Recycler**，Google对于列表视图的缓存的设计一直非常考究值得我们学习和研究。而网页的H5和火热的RN对于复杂的列表视图的渲染性能不好从这里面其实也可以寻找到一些原因。
### 总流程图
放上一张[Bugly的一篇博客](https://segmentfault.com/a/1190000007331249)对RecyclerView的缓存的流程图吧（自己画发现差不多就直接挪过来了...若侵立删）
![总流程](/assets/img/posts/3076e433cdaf8f66.jpg)

### 源码分析
如果看过上一篇博客的人应该还记得我们当中提到了和缓存机制有关的那个函数。
```
void layoutChunk(RecyclerView.Recycler recycler, RecyclerView.State state,
                     LayoutState layoutState, LayoutChunkResult result) {
        //next方法很重要
        View view = layoutState.next(recycler);
        //执行addView
        //执行measureChild操作
```
这里再放上这行代码，没错就是next函数。
```
View next(RecyclerView.Recycler recycler) {
            //默认mScrapList=null，但是执行layoutForPredictiveAnimations方法的时候不会为空
            if (mScrapList != null) {
                return nextViewFromScrapList();
            }
            //重要，从recycler获得View,mScrapList是被LayoutManager持有，recycler是被RecyclerView持有
            final View view = recycler.getViewForPosition(mCurrentPosition);
            mCurrentPosition += mItemDirection;
            return view;
        }
```
而next函数这里也放了上来，其实可以看到，除了我们平常认知的RecyclerView中Recycler的缓存，这里其实还存在一级的缓存**mScrapList**，mScrapList是被LayoutManager持有，recycler是被RecyclerView持有。但是mScrapList其实一定程度上和动画有关，这里就不做分析了，所以可以看到，缓存的重头戏还是在RecyclerView中的内部类**Recycler**中。这里先对Recycler这个内部类大体了解一下。
```
public final class Recycler {
    final ArrayList<ViewHolder> mAttachedScrap = new ArrayList<>();
    ArrayList<ViewHolder> mChangedScrap = null;

    final ArrayList<ViewHolder> mCachedViews = new ArrayList<ViewHolder>();

    private final List<ViewHolder>
            mUnmodifiableAttachedScrap = Collections.unmodifiableList(mAttachedScrap);

    private int mRequestedCacheMax = DEFAULT_CACHE_SIZE;
    int mViewCacheMax = DEFAULT_CACHE_SIZE;

    RecycledViewPool mRecyclerPool;

    private ViewCacheExtension mViewCacheExtension;

    static final int DEFAULT_CACHE_SIZE = 2;
    ...
    }
    类的结构也比较清楚，这里可以清楚的看到我们后面讲到的四级缓存机制所用到的类都在这里可以看到：
    * 1.一级缓存：mAttachedScrap
    * 2.二级缓存：mCacheViews
    * 3.三级缓存：mViewCacheExtension
    * 4.四级缓存：mRecyclerPool
```

继续跟进getViewForPosition方法，其实可以发现最后进入的是tryGetViewHolderForPositionByDeadline方法。
```
/**
 * Attempts to get the ViewHolder for the given position, either from the Recycler scrap,
 * cache, the RecycledViewPool, or creating it directly.
 **/
    /**
     * 注释写的很清楚，从Recycler的scrap，cache，RecyclerViewPool,或者直接create创建
     **/
    @Nullable
    ViewHolder tryGetViewHolderForPositionByDeadline(int position,
                                                     boolean dryRun, long deadlineNs) {
        if (position < 0 || position >= mState.getItemCount()) {
            throw new IndexOutOfBoundsException("Invalid item position " + position
                    + "(" + position + "). Item count:" + mState.getItemCount()
                    + exceptionLabel());
        }
        boolean fromScrapOrHiddenOrCache = false;
        ViewHolder holder = null;
        // 0) If there is a changed scrap, try to find from there
        if (mState.isPreLayout()) {
            //preLayout默认是false，只有有动画的时候才为true
            holder = getChangedScrapViewForPosition(position);
            fromScrapOrHiddenOrCache = holder != null;
        }
        // 1) Find by position from scrap/hidden list/cache
        if (holder == null) {
            holder = getScrapOrHiddenOrCachedHolderForPosition(position, dryRun);
            if (holder != null) {
                if (!validateViewHolderForOffsetPosition(holder)) {
                    //如果检查发现这个holder不是当前position的
                    // recycle holder (and unscrap if relevant) since it can't be used
                    if (!dryRun) {
                        // we would like to recycle this but need to make sure it is not used by
                        // animation logic etc.
                        holder.addFlags(ViewHolder.FLAG_INVALID);
                        //从scrap中移除
                        if (holder.isScrap()) {
                            removeDetachedView(holder.itemView, false);
                            holder.unScrap();
                        } else if (holder.wasReturnedFromScrap()) {
                            holder.clearReturnedFromScrapFlag();
                        }
                        //放到ViewCache或者Pool中
                        recycleViewHolderInternal(holder);
                    }
                    //至空继续寻找
                    holder = null;
                } else {
                    fromScrapOrHiddenOrCache = true;
                }
            }
        }
        if (holder == null) {
            final int offsetPosition = mAdapterHelper.findPositionOffset(position);
            if (offsetPosition < 0 || offsetPosition >= mAdapter.getItemCount()) {
                throw new IndexOutOfBoundsException("Inconsistency detected. Invalid item "
                        + "position " + position + "(offset:" + offsetPosition + ")."
                        + "state:" + mState.getItemCount() + exceptionLabel());
            }

            final int type = mAdapter.getItemViewType(offsetPosition);
            // 2) Find from scrap/cache via stable ids, if exists
            if (mAdapter.hasStableIds()) {
                holder = getScrapOrCachedViewForId(mAdapter.getItemId(offsetPosition),
                        type, dryRun);
                if (holder != null) {
                    // update position
                    holder.mPosition = offsetPosition;
                    fromScrapOrHiddenOrCache = true;
                }
            }
            //自定义缓存
            if (holder == null && mViewCacheExtension != null) {
                // We are NOT sending the offsetPosition because LayoutManager does not
                // know it.
                final View view = mViewCacheExtension
                        .getViewForPositionAndType(this, position, type);
                if (view != null) {
                    holder = getChildViewHolder(view);
                    if (holder == null) {
                        throw new IllegalArgumentException("getViewForPositionAndType returned"
                                + " a view which does not have a ViewHolder"
                                + exceptionLabel());
                    } else if (holder.shouldIgnore()) {
                        throw new IllegalArgumentException("getViewForPositionAndType returned"
                                + " a view that is ignored. You must call stopIgnoring before"
                                + " returning this view." + exceptionLabel());
                    }
                }
            }
            //pool
            if (holder == null) { // fallback to pool
                if (DEBUG) {
                    Log.d(TAG, "tryGetViewHolderForPositionByDeadline("
                            + position + ") fetching from shared pool");
                }
                holder = getRecycledViewPool().getRecycledView(type);
                if (holder != null) {
                    holder.resetInternal();
                    if (FORCE_INVALIDATE_DISPLAY_LIST) {
                        invalidateDisplayListInt(holder);
                    }
                }
            }
            //create
            if (holder == null) {
                long start = getNanoTime();
                if (deadlineNs != FOREVER_NS
                        && !mRecyclerPool.willCreateInTime(type, start, deadlineNs)) {
                    // abort - we have a deadline we can't meet
                    return null;
                }
                holder = mAdapter.createViewHolder(RecyclerView.this, type);
                if (ALLOW_THREAD_GAP_WORK) {
                    // only bother finding nested RV if prefetching
                    RecyclerView innerView = findNestedRecyclerView(holder.itemView);
                    if (innerView != null) {
                        holder.mNestedRecyclerView = new WeakReference<>(innerView);
                    }
                }

                long end = getNanoTime();
                mRecyclerPool.factorInCreateTime(type, end - start);
            }
        }
        ....
        return holder;
    }
```
删除了得到holder后的代码（其实还想再删点的...），本篇博客主要是对缓存机制源码的分析。对于源码的一个方法第一眼先看一下方法的注释，这里专门把方法的注释放了上来，可以发现注释写的很清楚**从Recycler的scrap，cache，RecyclerViewPool,或者直接create创建**，这可以说是对RecyclerView缓存流程的概述：**四级缓存**(不知道为什么官方的注释没有写上自定义缓存...)。接下来就一级一级分析吧。
```
 if (mState.isPreLayout()) {
            //preLayout默认是false，只有有动画的时候才为true
            holder = getChangedScrapViewForPosition(position);
            fromScrapOrHiddenOrCache = holder != null;
        }
```
首先可以看到这里有个判断，当为true的时候也可以拿到holder，但是这里我们没有并到常规缓存里面，首先可以看一下判断条件是对mInPreLayout变量的判断，mInPreLayout默认是false，只有有**动画**的时候才为true。其次对于getChangedScrapViewForPosition方法，其实是从Recycler类中的mChangedScrap获取ViewHolder，这也是为什么我们刚才没有将mChangedScrap放到常规缓存里面。
####  第一次尝试（从mAttachedScrap和mCacheView中）
```
if (holder == null) {
            holder = getScrapOrHiddenOrCachedHolderForPosition(position, dryRun);
            if (holder != null) {
                if (!validateViewHolderForOffsetPosition(holder)) {
                    //如果检查发现这个holder不是当前position的
  			...
                        //从scrap中移除
                        if (holder.isScrap()) {
                            removeDetachedView(holder.itemView, false);
                            holder.unScrap();
                        } else if (holder.wasReturnedFromScrap()) {
                            ...
                        }
                        //放到ViewCache或者Pool中
                        recycleViewHolderInternal(holder);
                    }
                    //至空继续寻找
                    holder = null;
                } else {
                    fromScrapOrHiddenOrCache = true;
                }
            }
        }
```
先大体看一下第一级缓存，可以看到，这里通过getScrapOrHiddenOrCachedHolderForPosition方法来获取ViewHolder，并检验holder的有效性，如果无效，则从mAttachedScrap中移除，并加入到mCacheViews或者Pool中，并且将holder至null，走下一级缓存判断。
```
holder = getScrapOrHiddenOrCachedHolderForPosition(position, dryRun);

//---------------------------------------------------------
ViewHolder getScrapOrHiddenOrCachedHolderForPosition(int position, boolean dryRun) {
        final int scrapCount = mAttachedScrap.size();

        // Try first for an exact, non-invalid match from scrap.
        //先从scrap中寻找
        for (int i = 0; i < scrapCount; i++) {
            final ViewHolder holder = mAttachedScrap.get(i);
            return holder;
           ...
        }
        //dryRun为false
        if (!dryRun) {
            //从HiddenView中获得，这里获得是View
            View view = mChildHelper.findHiddenNonRemovedView(position);
            if (view != null) {
                // This View is good to be used. We just need to unhide, detach and move to the
                // scrap list.
                //通过View的LayoutParam获得ViewHolder
                final ViewHolder vh = getChildViewHolderInt(view);
                //从HiddenView中移除
                mChildHelper.unhide(view);
                ....
                mChildHelper.detachViewFromParent(layoutIndex);
                //添加到Scrap中，其实这里既然已经拿到了ViewHolder，可以直接传vh进去
                scrapView(view);
                vh.addFlags(ViewHolder.FLAG_RETURNED_FROM_SCRAP
                        | ViewHolder.FLAG_BOUNCED_FROM_HIDDEN_LIST);
                return vh;
            }
        }

        // Search in our first-level recycled view cache.
        //从CacheView中拿
        final int cacheSize = mCachedViews.size();
        for (int i = 0; i < cacheSize; i++) {
            final ViewHolder holder = mCachedViews.get(i);
            // invalid view holders may be in cache if adapter has stable ids as they can be
            // retrieved via getScrapOrCachedViewForId
            //holder是有效的，并且position相同
            if (!holder.isInvalid() && holder.getLayoutPosition() == position) {
                if (!dryRun) {
                    mCachedViews.remove(i);
                }
                return holder;
            }
        }
        return null;
    }
```
这里可以看到也分了三个步骤：
* 1.从mAttachedScrap中获取
* 2.从HiddenView中获取
* 3.从CacheView获取
关键的代码注释我已经放上了，流程上可以用下面这个图来理解：
![第一次判断](/assets/img/posts/70f5cb6bd947681d.png)


####  第二次尝试(对应hasStablelds情况)
```
if (holder == null) {
		...
            final int type = mAdapter.getItemViewType(offsetPosition);
            // 2) Find from scrap/cache via stable ids, if exists
            if (mAdapter.hasStableIds()) {
                holder = getScrapOrCachedViewForId(mAdapter.getItemId(offsetPosition),
                        type, dryRun);
                if (holder != null) {
                    // update position
                    holder.mPosition = offsetPosition;
                    fromScrapOrHiddenOrCache = true;
                }
            }
           ....
        }
```
这里首先先看一个重点：**mAdapter.getItemViewType(offsetPosition);**熟悉的方法有木有，可以看到这里调用了我们平常使用RecyclerView进行多样式item的方法，也就是说前面对于一级缓存mAttachedScrap和mCacheViews是**不区分type**的，从现在开始的判断是区分type的缓存。这里对于我们研究多type类型的RecyclerView很有帮助。
接下来的判断可以看到很明显这是对于我们重写hasStableIds()方法为true的情况。
```
ViewHolder getScrapOrCachedViewForId(long id, int type, boolean dryRun) {
        // Look in our attached views first
        //
        final int count = mAttachedScrap.size();
        for (int i = count - 1; i >= 0; i--) {
            //在attachedScrap中寻找
            final ViewHolder holder = mAttachedScrap.get(i);
            if (holder.getItemId() == id && !holder.wasReturnedFromScrap()) {
                //id相同并且不是从scrap中返回的
                if (type == holder.getItemViewType()) {
                    holder.addFlags(ViewHolder.FLAG_RETURNED_FROM_SCRAP);
                    if (holder.isRemoved()) {
                        // this might be valid in two cases:
                        // > item is removed but we are in pre-layout pass
                        // >> do nothing. return as is. make sure we don't rebind
                        // > item is removed then added to another position and we are in
                        // post layout.
                        // >> remove removed and invalid flags, add update flag to rebind
                        // because item was invisible to us and we don't know what happened in
                        // between.
                        if (!mState.isPreLayout()) {
                            holder.setFlags(ViewHolder.FLAG_UPDATE, ViewHolder.FLAG_UPDATE
                                    | ViewHolder.FLAG_INVALID | ViewHolder.FLAG_REMOVED);
                        }
                    }
                    return holder;
                } else if (!dryRun) {
                    // if we are running animations, it is actually better to keep it in scrap
                    // but this would force layout manager to lay it out which would be bad.
                    // Recycle this scrap. Type mismatch.
                    //从scrap中移除
                    mAttachedScrap.remove(i);
                    removeDetachedView(holder.itemView, false);
                    //加入cacheView或者pool
                    quickRecycleScrapView(holder.itemView);
                }
            }
        }
        //从cacheView中找
        // Search the first-level cache
        final int cacheSize = mCachedViews.size();
        for (int i = cacheSize - 1; i >= 0; i--) {
            final ViewHolder holder = mCachedViews.get(i);
            if (holder.getItemId() == id) {
                if (type == holder.getItemViewType()) {
                    if (!dryRun) {
                        //从cache中移除
                        mCachedViews.remove(i);
                    }
                    return holder;
                } else if (!dryRun) {
                    //从cacheView中移除，但是放到pool中
                    recycleCachedViewAt(i);
                    return null;
                }
            }
        }
        return null;
    }
```
可以看到这里的判断其实和上面那一次差不多，需要注意的是**多了对于id的判断和对于type的判断**，也就是当我们将hasStableIds()设为true后需要重写holder.getItemId() 方法，来为每一个item设置一个单独的id。具体流程图如下：
![第二次判断](/assets/img/posts/fad46612984f6b4e.png)

####  第三次尝试(对应于自定义缓存)
其实这种对于我们平常的使用来说已经很陌生了，甚至很多人都不知道RecyclerView的这一项特性。
```
//自定义缓存
            if (holder == null && mViewCacheExtension != null) {
                // We are NOT sending the offsetPosition because LayoutManager does not
                // know it.
                final View view = mViewCacheExtension
                        .getViewForPositionAndType(this, position, type);
                if (view != null) {
                    holder = getChildViewHolder(view);
                    if (holder == null) {
                        throw new IllegalArgumentException("getViewForPositionAndType returned"
                                + " a view which does not have a ViewHolder"
                                + exceptionLabel());
                    } else if (holder.shouldIgnore()) {
                        throw new IllegalArgumentException("getViewForPositionAndType returned"
                                + " a view that is ignored. You must call stopIgnoring before"
                                + " returning this view." + exceptionLabel());
                    }
                }
            }
```
这里对于流程的理解没有什么好说的，我们可以看一下这个自定义缓存的类**ViewCacheExtension**。
```
public abstract static class ViewCacheExtension {
    public abstract View getViewForPositionAndType(Recycler recycler, int position, int type);
}
```
可以看到这里类很**恐怖**，为什么这样说哪？
>1.首先这个类基本上没有什么限制，也就是说无论是缓存使用的数据结构还有缓存算法(LRU还是什么)完全自定义，都由开发者自己决定，这一点可以说既给了开发者很大的便利，也给开发者带来了很大的隐患。
>2.对于平常的缓存，我们的理解在怎么说至少**get-add|push-pop**都是成对出现，为什么这样说的，也就是缓存至少有进也有出。而这里可以看到这里的抽象类只定义了出的方法，也就是**只出不进**，进的时机，大小，时效等完全没有规定。

####  第四次尝试(对应于Pool)
终于到了最后一次的尝试，这个缓存是针对Pool的，可以说**RecyclerView内部提供的Pool是RecyclerView的一大特性**，这也是和ListView不同的地方，RecyclerView提供了这种缓存形式，支持多个RecyclerView之间复用View，也就是说通过自定义Pool我们甚至可以实现整个应用内的RecyclerView的View的复用。
```
if (holder == null) { // fallback to pool
                ......
                holder = getRecycledViewPool().getRecycledView(type);
               ......
            }
```
同样这里对于流程没有什么好说的了，可以看一下RecyclerPool的类的结构。
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

    private int mAttachCount = 0;
    ...
    public ViewHolder getRecycledView(int viewType) {
        final ScrapData scrapData = mScrap.get(viewType);
        if (scrapData != null && !scrapData.mScrapHeap.isEmpty()) {
            final ArrayList<ViewHolder> scrapHeap = scrapData.mScrapHeap;
            return scrapHeap.remove(scrapHeap.size() - 1);
        }
        return null;
    }
    ......
  }
```
可以看到RecyclerdViewPool内部使用到了Google推荐的数据结构类型**SparseArray**，而SparseArray内部的**key**就是我们的**ViewType**，而**value**存放的是**ArrayList<ViewHolder>**。而默认的每个ArrayList<ViewHolder>的大小是5个。这里还有一个要注意的点就是**getRecycledView**这个方法可以看到拿到viewholder其实是通过remove拿到的，也就是通过remove拿到的。
#### 最终创建
```
//create
            if (holder == null) {
                ......
                holder = mAdapter.createViewHolder(RecyclerView.this, type);
                ......
            }
```
终于看到了我们经常重写的方法**createViewHolder**，当所有的的尝试从缓存中获取都失败后，只能调用我们自己重写的createViewHolder方法，重新创建一个。

### 总结
本篇博客主要从源码的角度将RecyclerView内部的缓存获取的流程梳理了一遍，对于RecyclerView的缓存机制还远远不止如此，后面还会从别的角度学习RecyclerView的缓存机制。从这篇博客主要能看到以下几点：
>1.RecyclerView内部大体可以分为四级缓存：mAttachedScrap,mCacheViews,ViewCacheExtension,RecycledViewPool.
>2.mAttachedScrap,mCacheViews在第一次尝试的时候只是对View的复用，并且不区分type，但在第二次尝试的时候是区分了Type，是对于ViewHolder的复用，ViewCacheExtension,RecycledViewPool是对于ViewHolder的复用，而且区分type。
>3.如果缓存ViewHolder时发现超过了mCachedView的限制，会将最老的ViewHolder(也就是mCachedView缓存队列的第一个ViewHolder)移到RecycledViewPool中。

##### 相关
>基于AOP的RecyclerView复杂楼层样式的开发框架，楼层打通，支持组件化，支持MVP(不用每次再写Adapter了～)-[EMvp](https://github.com/DrownCoder/EMvp)
>Star👏支持一下～
>欢迎提issues讨论～
