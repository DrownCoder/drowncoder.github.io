---
title: "色彩天气APP-MVP初体验"
date: 2017-09-26 00:31:00+08:00
categories: ["Android设计模式"]
source_name: "色彩天气APP-MVP初体验"
jianshu_views: 450
jianshu_url: "https://www.jianshu.com/p/7b511820581e"
---
一直理论上看mvc,mvp,mvvm，但是实际上总是用的mvc，没有真正意义上写过mvp的代码，所以实际动手写了一个用mvp实现的小项目。

### 技术点介绍
1.mvp模式
2.原生retroft2
3.百度sdk
4.自定义View
5.sqllite

### 功能介绍
1.根据ip，通过百度sdk定位城市
2.获得城市天气，支持天气预报
3.查询城市
4.本地备份已查询的城市列表
5.删除查询城市
6.随机变换背景颜色
7.等
[图片上传失败...(image-c9a721-1520074990545)]

### mvp感受（优点）
1.贯彻**面向接口编程**，项目读起来更清晰。
2.Activity只负责view责任，将数据处理从Activity移除，**大量减轻Activity负重**。
3.model中的数据层只负责数据处理，不关心View的对应显示，这样可以将model层进行复用。
4.presenter负责view层和model的交互，说到底就是讲原来本该在Activity中写的数据处理分散到presenter层进行处理。
6.业务逻辑更清晰，高内聚，低耦合。
7.当工程mvp模式成熟后，维护和后期的开发很容易，远比mvc容易的多。

### mvp感受（缺点）
1.入门感觉麻烦，刚开始写mvp模式是拒绝的。。。本来一个Activity文件就可以解决的问题，却要强行分成至少3+的文件，不愿意动手这样做。(但当架子搭好后会发现很方便)
2.文件量变多，还是上面的问题，会多出很过文件，用来分清职责。
3.presenter也会过于膨胀。

下面就以demo中的一个功能模块天气来展示mvp模式。
### 1.实现bean
这个是基本的，用GsonFormat完成就够了。
### 2.实现业务model层biz
#### (1) 定义功能接口IWeatherBiz
    public interface IWeatherBiz {
    public String getWeatherInfo(String cityName ,OnRequestListener onRequestListener);
	}

这里在接口中定义业务逻辑需要实现的功能，对应当阅读代码的时候，完全可以先从接口入手，多少个方法一看，大概就能明白这个业务model的功能是干什么的，不用在冗长的model代码中一片一片翻阅来理解业务功能。
#### (2) 实现功能model类WeatherBiz
    public class WeatherBiz implements IWeatherBiz{
    @Override
    public String getWeatherInfo(String cityName , final OnRequestListener onRequestListener) {
        Retrofit retrofit = new Retrofit.Builder()
                .addConverterFactory(GsonConverterFactory.create())
                .baseUrl(BASE_WEATHER_API)
                .build();
        WeatherService service = retrofit.create(WeatherService.class);
        Call<WeatherInfo> model = service.getWeatherInfo(cityName);
        model.enqueue(new Callback<WeatherInfo>() {
            @Override
            public void onResponse(Call<WeatherInfo> call, Response<WeatherInfo> response) {
                if (response.body().getStatus() == AppConstants.STATUS_OK) {
                    onRequestListener.onRequestSuccess(response.body());
                }else{
                    onRequestListener.onRequestFailed();
                }
            }

            @Override
            public void onFailure(Call<WeatherInfo> call, Throwable t) {
                onRequestListener.onRequestFailed();
            }
        });
        return  null;
    }
	}

在业务model类中，实现IWeatherBiz接口，对应实现接口中定义的方法，实现相应的业务逻辑。

### （3）定义View的接口IWeatherView
    public interface IWeatherView {
    String getCityName();

    void showWeatherInfo(String date, String temp, String type);

    void showCityName(City city);

    void showCityName(String name);

    void showLoading();

    void hideLoading();

    void showWeather();
	}
Activity中需要做什么，在接口中先定义好，Activity通过实现接口中的方法实现相应的对View的操作。

### （4）定义Presenter
    public class WeatherInfoPresenter {
    private Context mContext;
    private WeatherInfo mWeatherInfo;
    private IWeatherBiz weatherBiz;
    private IWeatherView weatherView;

    private BackupBiz mDao;

    public WeatherInfoPresenter(Context context, IWeatherView weatherView) {
        this.mContext = context;
        this.weatherView = weatherView;
        this.weatherBiz = new WeatherBiz();
        this.mDao = new BackupBiz(mContext);
    }

    public WeatherInfo getWeatherInfo() {
        weatherView.showLoading();
        weatherBiz.getWeatherInfo(weatherView.getCityName(), new OnRequestListener<WeatherInfo>() {
            @Override
            public void onRequestSuccess(WeatherInfo info) {
                mWeatherInfo = info;
                mDao.insertOrUpdateCity(new CityWeather(info.getData().getCity()
                        , info.getData().getWendu(), info.getData().getForecast().get(0).getType()), "1");
                showDataWeather(0);
            }

            @Override
            public void onRequestFailed() {
            }
        });
        return mWeatherInfo;
    }

    public void showWeatherInfo(int i) {
        if (mWeatherInfo != null) {
            showDataWeather(i);
        }
    }

    private void showDataWeather(int i) {
        switch (i) {
            case -1: {//昨天
                weatherView.showWeatherInfo(
                        mWeatherInfo.getData().getYesterday().getDate(),
                        mWeatherInfo.getData().getYesterday().getHigh().substring(3),
                        mWeatherInfo.getData().getYesterday().getType());
                break;
            }
            case 0: {
                weatherView.showWeatherInfo(
                        mWeatherInfo.getData().getForecast().get(0).getDate(),
                        mWeatherInfo.getData().getWendu() + "℃",
                        mWeatherInfo.getData().getForecast().get(0).getType());
                break;
            }
            default: {
                weatherView.showWeatherInfo(
                        mWeatherInfo.getData().getForecast().get(i).getDate(),
                        mWeatherInfo.getData().getForecast().get(i).getHigh().substring(3),
                        mWeatherInfo.getData().getForecast().get(i).getType());
                break;
            }
        }
    }
	}

可以看到Presenter作为mvp中的枢纽层，可以看到他的成员变量包含WeatherInfo,IWeatherBiz,IWeatherView，包含了model,biz,view,所以将对应的业务逻辑通过biz处理完成后，需要进行UI操作的，通过IWeatherView进行操作，这样便完成了数据层和UI之间通过presenter通信。

### （4）Activity OR Fragment
这里主要要记得在Activity中初始化presenter并且实现IWeatherView接口中的方法。

这里给出具体Demo地址[MVPDemo](https://github.com/DrownCoder/MVPDemo)
