　　前两天用leakcanary检查自己做的应用时，发现居然报内存泄漏的错误，而且内存泄漏出现的原因是由于Volley使
用的问题，查看leakcanary打出的Log发现是由于Volley中的Listener导致，这让我很疑惑，为什么开源的框架Volley怎么会出现内存泄漏这种问题。  

　　在网上搜索了一下相关问题，发现出现这种问题的人还真不少，解决的方法也有很多种，列举一下我查到的解决方法：  
1.升级Volley包，有一个博客说将Volley的jar包升级一下版本（感觉不靠谱，没有试）  
2.使用单例模式，使用ApplicationContext,我看了一下我的代码，发现我用的就是单例模式，在Application中初始化RequestQueue，所以这种方法不能解决我的问题。  
3.**重点：**  
在一篇关于这个问题讨论的帖子中我发现了一条评论，感觉他说的很有道理，这个人的评论是这样的：    
>我觉得，楼上回复的都不是重点！Queue 用单例来封装是对的，但是内存泄漏明显不是因为是不是单例原因造成的，是因为楼主写的 new Response.Listener<String>()  这句使用了内部匿名类，因为他初始化的时候是在HeapTestActivity 里面自动生成一个内部类，那么这个内部类没有执行完毕的时候，是持有HeapTestActivity 的引用的，导致HeapTestActivity 不能被回收，从而导致内存泄漏！  

**分析：**  
我感觉这个人的解释我很赞同，内存泄漏很大一部分出现的原因就是因为匿名内部类持有外部类的引用导致，外部类不能被垃圾回收器回收，所以导致内存泄漏。在这个例子里面，因为Volley使用的GsonRequest执行的是网络操作，Android中网络操作和UI线程是异步的，所以，可能在网络操作中，由于耗时操作没有执行完毕，导致Listener持有的Activity实例不能被销毁，而导致内存泄漏。  

**解决方式：**  
既然是由于Listener持有Activity的引用导致Activity不能被及时销毁，那么就要用到JAVA的四种引用中的**WeakReference**了，这个解决方式的是我收到的一篇博客，[原文链接](http://blog.csdn.net/u013475663/article/details/60139939)，其实思想很简单，就是实现以下Volley中的Listener和ErrorListener接口，在其中使用WeakReference在初始化Listener中持有Activity的引用，这样就可以解决Volley中内存泄漏的问题了  
**（实测原来的内存泄漏没有了）**  

为了便于方便，我将郭神提供的[GsonRequset](http://blog.csdn.net/guolin_blog/article/details/17612763)二次封装了一下，方便下次使用。  

```
public class GsonRequest<T> extends Request<T> {

    private final Response.Listener<T> mListener;

    private Gson mGson;

    private Class<T> mClass;

    public GsonRequest(int method, String url, Class<T> clazz, WeakListener<T> listener,
                       WeakErrorListener errorListener) {
        super(method, url, errorListener);
        mGson = new Gson();
        mClass = clazz;
        mListener = listener;
    }

    public GsonRequest(String url, Class<T> clazz, WeakListener<T> listener,
                       WeakErrorListener errorListener) {
        this(Method.GET, url, clazz, listener, errorListener);
    }

    @Override
    protected Response<T> parseNetworkResponse(NetworkResponse response) {
        try {
            String jsonString = new String(response.data,
                    HttpHeaderParser.parseCharset(response.headers));
            return Response.success(mGson.fromJson(jsonString, mClass),
                    HttpHeaderParser.parseCacheHeaders(response));
        } catch (UnsupportedEncodingException e) {
            return Response.error(new ParseError(e));
        }
    }

    @Override
    protected void deliverResponse(T response) {
        mListener.onResponse(response);
    }

    public static abstract class WeakListener<T> implements Response.Listener<T> {
        private final WeakReference<Activity> activityWeakReference;

        public WeakListener(Activity activity) {
            activityWeakReference = new WeakReference<Activity>(activity);
        }

        @Override
        public abstract void onResponse(T response);
    }

    public static abstract class WeakErrorListener implements Response.ErrorListener {
        private final WeakReference<Activity> activityWeakReference;

        public WeakErrorListener(Activity activity) {
            activityWeakReference = new WeakReference<Activity>(activity);
        }

        @Override
        public abstract void onErrorResponse(VolleyError error);
    }

}
```
