>1.[Volley源码分析（一）](http://www.jianshu.com/p/b409f2bde354)
>2.[Volley源码分析（二）](http://www.jianshu.com/p/80a73df1eb25)
>3.[Volley源码分析（三）](http://www.jianshu.com/p/1c7071e44f61)
>4.[XVolley-基于Volley的封装的工具类](http://www.jianshu.com/p/a6a038dee1d1)

上一篇分析完了Volley.newRequestqueue()方法。方法最后执行到了requestqueue.start()方法
 

```
 /**
     * Starts the dispatchers in this queue.
     */
    public void start() {
        //停止当前所有线程
        stop();  // Make sure any currently running dispatchers are stopped.
        // Create the cache dispatcher and start it.
        //创建一个缓冲线程，并start
        mCacheDispatcher = new CacheDispatcher(mCacheQueue, mNetworkQueue, mCache, mDelivery);
        mCacheDispatcher.start();

        // Create network dispatchers (and corresponding threads) up to the pool size.
        //创建4个网络请求线程
        for (int i = 0; i < mDispatchers.length; i++) {
            NetworkDispatcher networkDispatcher = new NetworkDispatcher(mNetworkQueue, mNetwork,
                    mCache, mDelivery);
            mDispatchers[i] = networkDispatcher;
            networkDispatcher.start();
        }
    }
```

首先看stop方法

```
/**
     * Stops the cache and network dispatchers.
     */
    public void stop() {
        if (mCacheDispatcher != null) {
            mCacheDispatcher.quit();
        }
        for (final NetworkDispatcher mDispatcher : mDispatchers) {
            if (mDispatcher != null) {
                mDispatcher.quit();
            }
        }
    }
```

可以看到，stop方法里将所有的线程都quit掉了。

stop方法执行完毕后，会创建一个CacheDispatcher对象和NetworkDispatcher对象的数组，这里先提前说明一下，这两个对象都是继承的Thread类（后面会单独分析这两个类）再通过名字就很好理解了，这里stop后会创建一个缓存线程和4个网络线程，并调用start方法。

**4个线程的来历**：可以看下RequestQueue是我们在创建RequestQueue时的构造方法,默认调用的是第一个构造方法，对应的DEFAULT_NETWORK_THREAD_POOL_SIZE=4

```
public RequestQueue(Cache cache, Network network) {
        /**
         * 默认线程池大小=4
         */
        this(cache, network, DEFAULT_NETWORK_THREAD_POOL_SIZE);
    }
    
	public RequestQueue(Cache cache, Network network, int threadPoolSize) {
        this(cache, network, threadPoolSize,
                //Looper.getMainLooper()对应主线程，所以请求成功后的接口回调对应是在主线程中执行。
                new ExecutorDelivery(new Handler(Looper.getMainLooper())));
    }
    
	public RequestQueue(Cache cache, Network network, int threadPoolSize,ResponseDelivery delivery) {
        mCache = cache;
        mNetwork = network;
        mDispatchers = new NetworkDispatcher[threadPoolSize];
        mDelivery = delivery;
    }
```

分析完start方法，现在分析requestqueue的add方法。

```
public <T> Request<T> add(Request<T> request) {
        // Tag the request as belonging to this queue and add it to the set of current requests.
        request.setRequestQueue(this);
        //mCurrentRequest是一个HashSet,不是线程安全的，所以进行加锁操作，保证同时只能加一个
        synchronized (mCurrentRequests) {
            mCurrentRequests.add(request);
        }

        // Process requests in the order they are added.
        //添加序列号，这里用到了AtomicInteger，是一个线程安全的Integer，适用于高并发的Integer加减
        request.setSequence(getSequenceNumber());
        //添加一个Log信息
        request.addMarker("add-to-queue");

        // If the request is uncacheable, skip the cache queue and go straight to the network.
        //判断request是否需要缓存，默认是需要的
        if (!request.shouldCache()) {
            //不需要缓存的话直接加入队列，使用的是PriorityBlockingQueue---一个基于优先级堆的无界的并发安全的优先级队列
            mNetworkQueue.add(request);
            return request;
        }

        // Insert request into stage if there's already a request with the same cache key in flight.
        //mWaitingRequest 对应一个map<key,queue<request>>
        synchronized (mWaitingRequests) {
            //key对应着url
            String cacheKey = request.getCacheKey();
            if (mWaitingRequests.containsKey(cacheKey)) {
                //如果已经有一个相同的请求已经在等待队列里，则将现在这个请求放入相同key的等待队列中
                // There is already a request in flight. Queue up.
                Queue<Request<?>> stagedRequests = mWaitingRequests.get(cacheKey);
                //没有则new一个
                if (stagedRequests == null) {
                    stagedRequests = new LinkedList<>();
                }
                stagedRequests.add(request);
                mWaitingRequests.put(cacheKey, stagedRequests);
                if (VolleyLog.DEBUG) {
                    VolleyLog.v("Request for cacheKey=%s is in flight, putting on hold.", cacheKey);
                }
            } else {
                // Insert 'null' queue for this cacheKey, indicating there is now a request in
                // flight.
                //没有的话则插入一个key-null的信息，当为null表明这个key对应的请求就这一个，由于需要缓存，则加入缓存队列
                mWaitingRequests.put(cacheKey, null);
                mCacheQueue.add(request);
            }
            return request;
        }
    }
```

**第一步**：首先将request加入mCurrentRequests。这里注意：
**mCurrentRequests是一个HashSet,HashSet底层是一个HashMap,所以不是线程安全的，这里为了线程安全，利用synchronized关键字实现了加锁操作。**
**第二步**：给request添加了序列号。
**这里用到了AtomicInteger，是一个线程安全的Integer，适用于高并发的Integer加减**

```
/**
     * Gets a sequence number.
     */
    public int getSequenceNumber() {
        return mSequenceGenerator.incrementAndGet();
    }
    /**
     * Atomically increments by one the current value.
     *
     * @return the updated value
     */
    public final int incrementAndGet() {
        return U.getAndAddInt(this, VALUE, 1) + 1;
    }
```

可以看到，这里利用AtomicInteger，每次获取的序列号的时候，增加1。
**第三步**：判断request是否需要缓存,每一个新建的request默认都是需要缓存的，如果不需要，则需要显式的调研request的setShouldCache方法。这里如果不需要缓存，则直接将request加入网络请求队列（如下代码所示）。这里使用的是PriorityBlockingQueue---**一个基于优先级堆的无界的并发安全的优先级队列**。

```
if (!request.shouldCache()) {
            //不需要缓存的话直接加入队列，使用的是PriorityBlockingQueue---一个基于优先级堆的无界的并发安全的优先级队列
            mNetworkQueue.add(request);
            return request;
        }
```

**第四步**：如果需要缓存，这里对应需要插入到两个地方mWaitingRequests和mCacheQueue，这里由于mWaitingRequests是一个HashMap，所以同样，需要通过synchronized关键字进行加锁操作。这里分细一点看：

```
String cacheKey = request.getCacheKey();
            if (mWaitingRequests.containsKey(cacheKey)) {
                //如果已经有一个相同的请求已经在等待队列里，则将现在这个请求放入相同key的等待队列中
                // There is already a request in flight. Queue up.
                Queue<Request<?>> stagedRequests = mWaitingRequests.get(cacheKey);
                //没有则new一个
                if (stagedRequests == null) {
                    stagedRequests = new LinkedList<>();
                }
                stagedRequests.add(request);
                mWaitingRequests.put(cacheKey, stagedRequests);
                if (VolleyLog.DEBUG) {
                    VolleyLog.v("Request for cacheKey=%s is in flight, putting on hold.", cacheKey);
                }
            }
```

1）这里mWaitingRequest对应的数据结构是`map<key,queue<request>>`，key对应的是url。首先判断mWaitingRequest中是否存在相同的url的request，如果存在，则取出存放这种url的requestqueue，存在这个url，但对应的queue为空，则new一个，并且将这个request加入queue,并将queue加入mWatingRequest。

```
 else {
                // Insert 'null' queue for this cacheKey, indicating there is now a request in
                // flight.
                //没有的话则插入一个key-null的信息，当为null表明这个key对应的请求就这一个，由于需要缓存，则加入缓存队列
                mWaitingRequests.put(cacheKey, null);
                mCacheQueue.add(request);
            }
```

2）如果不存在，则插入一个key-null到mWaitingRequest中，并将这个请求加入mCacheQueue缓存队列。

所以这里一个需要缓存的request进入情况就很好分析了，一个新的request加入进来，对应的，mWaitingRequest存放一个key-null。当同样的一个url的request进入的时候，就会放到mWaitingRequest中等待，而这时候mWaitingRequest存在该url的队列，只不过queue为null，这时候就会new一个新的queue放入mWaitingRequest,等下次有同样的url进入的时候，就会直接加入这个队列中等待。
