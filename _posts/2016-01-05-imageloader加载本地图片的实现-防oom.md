---
title: ImageLoader加载本地图片的实现————防OOM
date: 2017-09-26 00:30:54+08:00
categories: ["Android基础"]
source_name: "ImageLoader加载本地图片的实现————防OOM"
jianshu_views: 866
jianshu_url: "https://www.jianshu.com/p/93c69782357a"
---
这段时间，项目功能做完了，但是一直被OOM的问题困扰，在同样的代码在模拟机上可以运行，但在真机上却无法运行，报OOM，于是，最近开始接触关于OOM的相关问题，今天先总结一下关于ImageLoader的实现。
**实现ImageLoader主要用到了下面几个知识点：**
1.缓存LruCache。
2.线程池ExecutorService。
3.算法实现调度方式优化：LIFO（后进先出），FIFO（先进先出）。
4.任务队列LinkedList< Runnable >
5.后台轮询线程mPoolThread。
6.Handler的消息通讯。

知识点总结完毕后，说一下这个实现思路。
**ImageLoader实现思路：**
ImagLoader总体来说优化方式有几个点：
1.图片加载策略：使用LIFO而不是FIFO（一共有1000张图片，当你要查看第900张时肯定不能加载900张图片来显示第900张，可以只加载900张开始的图片，前面的图片不用加载）
2.图片压缩策略：对一个需要加载的图片，对ImageView的组件大小进行判断，和图片的实际大小进行比对，当图片过大时，利用Options进行压缩，压缩完成后再使用。
3.使用LruCache：设定一个固定大小的缓存空间（一般为dalvik虚拟机为应用分配的内存的1/8），当新的图片加载完成后先放入缓存，以后每次需要加载图片前，先到缓存中查找是否存在该图片，如果有，则直接从缓存中去，如果没有，再加载，这样避免了才加载完成不久的图片多次加载。
4.使用线程池，因为Android不允许在UI线程中执行耗时操作，所以加载图片时需要在新的线程中执行，但是，每加载一个图片就需要执行一个线程，那么大量图片加载的时候会占用大量内存，所以使用线程池，将固定同一时间只允许一定数量的线程在后台运行（自己设定，数量不要太大，3个左右），所有线程先加入线程池中。
用户传入url（图片地址）-> Bitmap
**图片查找思路：**
1.url->LruCache查找
->找到则返回Bitmap（这样避免同一张图片多次加载）
->找不到 ->url -> Task -> TaskQueue且发送一个通知给后台轮询线程
**2.图片加载思路：**
Task -> Run() 根据url 加载图片
1.获取图片显示大小
2.使用Options对图片进行压缩（防止图片过大导致OOM）
3.加载图片且放入LruCache（避免同一张图片多次加载）
**后台轮询线程：**
TaskQueue -> Task -> 线程池去执行（Handler+Looper+Message）

代码实现：
**声明变量：**

```
/**
*使用单例模型
*/
private static ImageLoader mInstance;
	/**
	 * 图片缓存的核心对象
	 */
	private LruCache<String, Bitmap> mLruCache;
	/**
	 * 线程池
	 */
	private ExecutorService mThreadPool;
	private static final int DEAFULT_THREAD_COUNT = 1;
	/**
	 * 队列调度方式
	 */
	private Type mType = Type.LIFO;
	/**
	 * 任务队列
	 */
	private LinkedList<Runnable> mTaskQueue;
	/**
	 * 后台轮询线程
	 */
	private Thread mPoolThread;
	private Handler mPoolThreadHandler;
	/**
	 * UI线程中的Handler
	 */
	private Handler mUIHandler;
	/**
	*信号量，用于多线程之间的资源同步
	*/
	private Semaphore mSemaphorePoolThreadHandler = new Semaphore(0);
	
	private Semaphore mSemaphoreThreadPool;
	/**
	*枚举类型，用于加载策略
	*/
	public enum Type {
		FIFO, LIFO;
	}
```

**构造方法：**

```
private ImageLoader(int threadCount, Type type) {
		init(threadCount, type);//传入默认线程池的线程个数，和加载策略
	}

	/*
	 * 初始化操作
	 */
	private void init(int threadCount, Type type) {
		// 后台轮询线程
		mPoolThread = new Thread() {
			@Override
			public void run() {
				Looper.prepare();//给线程创建一个消息循环
				mPoolThreadHandler = new Handler() {
					@Override
					public void handleMessage(Message msg) {
						// 线程池取出一个任务去执行
						mThreadPool.execute(getTask());
						try {
							mSemaphoreThreadPool.acquire();
						} catch (InterruptedException e) {
							// TODO Auto-generated catch block
							e.printStackTrace();
						}
					}

				};
				//释放一个信号量
				mSemaphorePoolThreadHandler.release();
				Looper.loop();//使消息循环起作用，Looper.loop()内部会结束整个子线程的执行， 所以Looper.loop()之后的语句是不会运行的
			}
		};
		/*mPoolThread = new Thread(new Runnable() {
			
			@Override
			public void run() {
				// TODO Auto-generated method stub
				Looper.prepare();
				mPoolThreadHandler = new Handler() {
					@Override
					public void handleMessage(Message msg) {
						// 线程池取出一个任务去执行
						mThreadPool.execute(getTask());
						try {
							mSemaphoreThreadPool.acquire();
						} catch (InterruptedException e) {
							// TODO Auto-generated catch block
							e.printStackTrace();
						}
					}

				};
				//释放一个信号量
				mSemaphorePoolThreadHandler.release();
				Looper.loop();
			}
		});*/
		mPoolThread.start();

		// 获取我们应用的最大可用内存
		int MaxMemory = (int) Runtime.getRuntime().maxMemory();
		//设置缓存大小为最大可用内存的1/8
		int cacheMemory = MaxMemory / 8;
		mLruCache = new LruCache<String, Bitmap>(cacheMemory) {
			@Override
			protected int sizeOf(String key, Bitmap value) {// 重写此方法来衡量每张图片的大小
				return value.getRowBytes() * value.getHeight();//getRowBytes()获取Bitmap每一行所占用的内存字节数。
			}
		};
		
		//创建线程池
		mThreadPool = Executors.newFixedThreadPool(threadCount);//创建一个固定大小的线程池,线程池执行数量不能超过threadcount
		mTaskQueue = new LinkedList<Runnable>();
		mType = type;
		
		mSemaphoreThreadPool = new Semaphore(threadCount);//创建一个信号量为threadcount的许可集
	}
```

```
/**
	 * 从任务队列取出一个方法
	 * @return
	 */
	private Runnable getTask() {
		if(mType == Type.FIFO){//先进先出，则从队列头开始取
			return mTaskQueue.removeFirst();
		}else if(mType == Type.LIFO)
		{//后进先出，则从队尾开始取
			return mTaskQueue.removeLast();
		}
		return null;
	}
```

```
public static ImageLoader getInstance(int threadCount,Type type) {
		// 懒加载，单例模型，一次初始化后，不需要再初始化
		if (mInstance == null) {
			// 同步资源锁，防止不同线程多次调用初始化ImageLoader类，占用内存，提高效率
			synchronized (ImageLoader.class) {

				if (mInstance == null) {
					mInstance = new ImageLoader(threadCount, type);
				}
			}
		}
		return mInstance;
	}
```

```
/**
	 *根据path为imageView设置图片
	 * @param path
	 * @param imageView
	 */
	public void loadImage(final String path,final ImageView imageView){
	//为每个ImageView设置Tag防止图片加载位置错误
		imageView.setTag(path);
		if(mUIHandler == null){
			mUIHandler = new Handler(){
				public void handleMessage(Message msg) {
					//获取得到图片，为imageview回调设置图片
					ImgBeanHolder holder = (ImgBeanHolder) msg.obj;
					Bitmap bm = holder.bitmap;
					ImageView imageview = holder.imageView;
					String path = holder.path;
					//将path与gettag存储路径进行比较
					if(imageview.getTag().toString().equals(path)){
						imageview.setImageBitmap(bm);
					}
				};
			};
		}
		//根据path在缓存中获取Bitmap
		Bitmap bm = getBitmapFromLruCache(path);
		if(bm != null){
		//缓存中存在，在从使用缓存中的图片
			refreshBitmap(path, imageView, bm);
		}else{
		//缓存中不存在则加载图片
			addTask(new Runnable() {
				
				@Override
				public void run() {
					//加载图片
					//图片的压缩
					//1.获得图片需要显示的大小
					ImageSize imageSize = getImageViewSize(imageView);
					//2.压缩图片
					Bitmap bm = decodeSampledBitmapFromPath(path,imageSize.width,imageSize.height);
					//3.把图片加入到缓存
					addBitmapToLruCache(path,bm);
					
					refreshBitmap(path, imageView, bm);
					//释放一个信号量，使线程池可以进行再取一个任务执行
					mSemaphoreThreadPool.release();
				}

			});
		}
		
	}
	private void refreshBitmap(final String path,
			final ImageView imageView, Bitmap bm) {
		Message message =Message.obtain();//从整个Messge池中返回一个新的Message实例，在许多情况下使用它，因为它能避免分配新的对象，避免内存开销
		ImgBeanHolder holder = new ImgBeanHolder();
		holder.bitmap = bm;
		holder.path = path;
		holder.imageView = imageView;
		message.obj = holder;
		mUIHandler.sendMessage(message);
	}
	/**
	 * 将图片加入缓存
	 * @param path
	 * @param bm
	 */
	protected void addBitmapToLruCache(String path, Bitmap bm) {
		// TODO Auto-generated method stub
		if(getBitmapFromLruCache(path) == null){
			if(bm!=null){
				mLruCache.put(path, bm);
			}
		}
	}

	/**
	 * 根据图片需要显示的宽和高进行压缩
	 * @param path
	 * @param width
	 * @param height
	 * @return
	 */
	protected Bitmap decodeSampledBitmapFromPath(String path, int width,
			int height) {
		//获取图片的宽和高并不把图片加载到内存中
		BitmapFactory.Options options = new BitmapFactory.Options();
		options.inJustDecodeBounds = true;
		BitmapFactory.decodeFile(path,options);//options中保存图片的真实宽高
		
		options.inSampleSize = caculateInSampleSize(options,width,height);//处理得到压缩比例
		
		//使用获取到的InSampleSize再次解析图片
		options.inJustDecodeBounds = false;
		Bitmap bitmap = BitmapFactory.decodeFile(path,options);
		return bitmap;
	}
/**
 * 根据需求的宽和高以及图片实际的宽和高计算SampleSize
 * @param options
 * @param width
 * @param height
 * @return
 */
	private int caculateInSampleSize(Options options, int reqwidth, int reqheight) {
		int width = options.outWidth;
		int height = options.outHeight;
		int inSampleSize = 1;
		if(width >reqwidth || height > reqheight){
			int widthRadio = Math.round(width*1.0f/reqwidth);
			int heightRadio = Math.round(height*1.0f/reqheight);
			//比例可以根据自己的需要调整
			inSampleSize = Math.max(widthRadio, heightRadio);
		}
		
		return inSampleSize;
	}

	/**
	 * 根据imageView获取适当的压缩的宽和高
	 * @param imageView
	 * @return
	 */
	protected ImageSize getImageViewSize(ImageView imageView) {
		 ImageSize imageSize = new ImageSize();
		 DisplayMetrics displayMetrics = imageView.getContext().getResources().getDisplayMetrics();//将当前窗口的一些信息放在DisplayMetrics类中
		 
		 LayoutParams lp = imageView.getLayoutParams();
		 int width = imageView.getWidth();//获取imageView的实际宽度
		 if(width <= 0){
			 width = lp.width;//获取imageview在layout中声明的宽度
		 }
		 if(width <= 0){
			 //width = imageView.getMaxWidth();//检查最大值
			 width = getImageViewFieldValue(imageView,"mMaxWidth");
		 }
		 if(width <= 0){
			 width = displayMetrics.widthPixels;//屏幕宽度
		 }
		 
		 
		 int height = imageView.getHeight();//获取imageView的实际宽度
		 if(height <= 0){
			 height = lp.height;//获取imageview在layout中声明的宽度
		 }
		 if(height <= 0){
			// height = imageView.getMaxHeight();//检查最大值
			 height = getImageViewFieldValue(imageView,"mMaxHeight");
		 }
		 if(height <= 0){
			 height = displayMetrics.heightPixels;
		 }
		 
		 imageSize.width = width;
		 imageSize.height = height;
		 
		return imageSize;
	}
	/**
	 * 通过反射获取ImageView	的某个属性值
	 * @param object
	 * @param fieldName
	 * @return
	 */
	private static int getImageViewFieldValue(Object object,String fieldName){
		int value = 0;
		try {
		Field field = ImageView.class.getDeclaredField(fieldName);
		field.setAccessible(true);
		
		int fieldValue = field.getInt(object);
		if(fieldValue>0 && fieldValue<Integer.MAX_VALUE){
			value = fieldValue;
		}
		} catch (Exception e) {
		}
		return value;
	}
/**
 * 同步锁，只能由一个调用，防止多个同时调用，一次加入过多Runnable
 * @param runnable
 */
	private synchronized void addTask(Runnable runnable) {
		mTaskQueue.add(runnable);
		//if(mPoolThreadHandler == null) wait();
		try {
			if(mPoolThreadHandler == null)
			mSemaphorePoolThreadHandler.acquire();/信号量加1
		} catch (InterruptedException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		mPoolThreadHandler.sendEmptyMessage(0x110);
	}

	/**
	 * 根据path在缓存中获取Bitmap
	 * @param key
	 * @return
	 */
	private Bitmap getBitmapFromLruCache(String key) {
		return mLruCache.get(key);
	}
	private class ImageSize {
		int width;
		int height;
	}
	private class ImgBeanHolder{
		Bitmap bitmap;
		 ImageView imageView;
		 String path;
	}
```
实现ImageLoader类的实现后，加载本地图片，只需一句话：
	ImageLoader.getInstance(3, Type.LIFO).loadImage(
					url, ImageView);
还是很方便的。

这次ImageLoader的实现让我感受到OOM的重要性，内存的管理优化真的很重要，以后要注重这方面的问题的空白。
