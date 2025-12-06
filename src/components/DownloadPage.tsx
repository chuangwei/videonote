import { useState, useEffect } from "react";
import { open } from "@tauri-apps/plugin-dialog";
import { Download, Folder, CheckCircle2, XCircle, Loader2, Video, Youtube, FileVideo, ArrowRight } from "lucide-react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Progress } from "./ui/progress";
import { api } from "@/lib/api";

interface DownloadTask {
  taskId: string;
  url: string;
  savePath: string;
  status: "downloading" | "completed" | "failed" | "idle";
  message: string;
  progress: number;
  filePath?: string;
  title?: string;
  speed?: string;
  eta?: string;
}

export function DownloadPage() {
  const [url, setUrl] = useState("");
  const [savePath, setSavePath] = useState("");
  const [downloadTask, setDownloadTask] = useState<DownloadTask | null>(null);
  const [apiReady, setApiReady] = useState(false);

  // 检查 API 是否准备就绪
  useEffect(() => {
    api
      .healthCheck()
      .then(() => {
        console.log("API 健康检查通过");
        setApiReady(true);
      })
      .catch((error) => {
        console.error("API 健康检查失败:", error);
        // 2秒后重试
        setTimeout(() => {
          api.healthCheck().then(() => setApiReady(true)).catch(console.error);
        }, 2000);
      });
  }, []);

  // 轮询下载状态
  useEffect(() => {
    if (!downloadTask || downloadTask.status === "completed" || downloadTask.status === "failed") {
      return;
    }

    const intervalId = setInterval(async () => {
      try {
        const status = await api.getDownloadStatus(downloadTask.taskId);

        // 根据响应更新任务状态
        if (status.file_path) {
          setDownloadTask({
            ...downloadTask,
            status: "completed",
            message: status.message,
            progress: 100,
            filePath: status.file_path,
            title: status.title,
          });
        } else {
          // 仍在下载，更新消息和进度
          const progressData = status.progress;
          setDownloadTask({
            ...downloadTask,
            message: status.message,
            progress: progressData ? progressData.percent : downloadTask.progress,
            speed: progressData ? progressData.speed : undefined,
            eta: progressData ? progressData.eta : undefined,
          });
        }
      } catch (error) {
        console.error("获取下载状态失败:", error);
        setDownloadTask({
          ...downloadTask,
          status: "failed",
          message: "无法检查下载状态",
        });
      }
    }, 1000); // 缩短轮询间隔以获得更流畅的进度

    return () => clearInterval(intervalId);
  }, [downloadTask]);

  const handleSelectFolder = async () => {
    try {
      const selected = await open({
        directory: true,
        multiple: false,
        title: "选择保存文件夹",
      });

      if (selected) {
        setSavePath(selected as string);
      }
    } catch (error) {
      console.error("选择文件夹失败:", error);
    }
  };

  const handleDownload = async () => {
    if (!url || !savePath) {
      alert("请输入视频链接并选择保存位置");
      return;
    }

    try {
      setDownloadTask({
        taskId: "",
        url,
        savePath,
        status: "downloading",
        message: "正在启动下载...",
        progress: 0,
      });

      const response = await api.startDownload(url, savePath);

      if (response.success && response.task_id) {
        setDownloadTask({
          taskId: response.task_id,
          url,
          savePath,
          status: "downloading",
          message: response.message,
          progress: 0,
        });
      } else {
        setDownloadTask({
          taskId: "",
          url,
          savePath,
          status: "failed",
          message: response.message || "启动下载失败",
          progress: 0,
        });
      }
    } catch (error) {
      console.error("下载失败:", error);
      setDownloadTask({
        taskId: "",
        url,
        savePath,
        status: "failed",
        message: error instanceof Error ? error.message : "下载失败",
        progress: 0,
      });
    }
  };

  const handleReset = () => {
    setUrl("");
    setSavePath("");
    setDownloadTask(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-100 via-purple-50 to-blue-100 p-8 flex flex-col items-center justify-center font-sans">
      
      {/* 装饰背景光斑 */}
      <div className="fixed top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
        <div className="absolute top-[-20%] left-[-10%] w-[500px] h-[500px] rounded-full bg-purple-300/30 blur-[100px]" />
        <div className="absolute bottom-[-20%] right-[-10%] w-[500px] h-[500px] rounded-full bg-blue-300/30 blur-[100px]" />
      </div>

      {/* 头部区域 */}
      <div className="relative z-10 text-center mb-10 space-y-3">
        <div className="inline-flex items-center justify-center p-4 bg-white/40 backdrop-blur-md rounded-3xl shadow-lg border border-white/50 mb-4 transition-transform hover:scale-105 duration-300">
          <Video className="w-8 h-8 text-indigo-600 drop-shadow-md" />
        </div>
        <h1 className="text-4xl font-bold tracking-tight text-slate-800 drop-shadow-sm">
          VideoNote 下载助手
        </h1>
        <p className="text-slate-600 font-medium text-lg tracking-wide">
          构建您的专属本地知识库
        </p>
      </div>

      {/* 主要卡片区域 - Liquid Glass 风格 */}
      <Card className="relative z-10 w-full max-w-xl shadow-2xl border border-white/60 bg-white/40 backdrop-blur-2xl rounded-[2rem] overflow-hidden">
        <CardHeader className="pb-4">
          <CardTitle className="flex items-center justify-between px-2">
            <span className="text-xl text-slate-800 font-semibold">新任务</span>
            {!apiReady && (
              <span className="text-xs font-medium px-3 py-1.5 bg-amber-100/80 text-amber-700 rounded-full flex items-center gap-1.5 shadow-sm backdrop-blur-sm border border-amber-200/50">
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                服务启动中...
              </span>
            )}
          </CardTitle>
          <CardDescription className="text-slate-500 px-2 text-base">
            输入视频链接，选择保存位置，即可开始离线保存
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-8 p-8 pt-2">
          {/* 链接输入 */}
          <div className="space-y-3 group">
            <label className="text-sm font-semibold text-slate-700 ml-1 transition-colors group-focus-within:text-indigo-600">视频链接</label>
            <div className="relative transition-all duration-300 focus-within:scale-[1.01]">
              <Input
                type="url"
                placeholder="粘贴视频链接，例如 https://www.youtube.com/watch?v=..."
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                disabled={!!downloadTask && downloadTask.status === "downloading"}
                className="pl-11 h-12 rounded-2xl bg-white/50 border-white/60 focus:bg-white/80 shadow-inner backdrop-blur-sm focus-visible:ring-0 focus-visible:ring-offset-0 focus:ring-2 focus:ring-indigo-400/50 focus:border-indigo-300 transition-all text-slate-800 placeholder:text-slate-400"
              />
              <Youtube className="w-5 h-5 text-slate-500 absolute left-4 top-3.5 transition-colors group-focus-within:text-red-500" />
            </div>
          </div>

          {/* 路径选择 */}
          <div className="space-y-3 group">
            <label className="text-sm font-semibold text-slate-700 ml-1 transition-colors group-focus-within:text-indigo-600">保存位置</label>
            <div className="flex gap-3">
              <div className="relative flex-1 transition-all duration-300 focus-within:scale-[1.01]">
                <Input
                  type="text"
                  placeholder="请选择保存文件夹..."
                  value={savePath}
                  readOnly
                  className="pl-11 h-12 rounded-2xl bg-white/50 border-white/60 cursor-pointer hover:bg-white/60 shadow-inner backdrop-blur-sm focus-visible:ring-0 focus-visible:ring-offset-0 focus:ring-2 focus:ring-indigo-400/50 focus:border-indigo-300 transition-all text-slate-800 placeholder:text-slate-400"
                  onClick={!downloadTask || downloadTask.status !== "downloading" ? handleSelectFolder : undefined}
                />
                <Folder className="w-5 h-5 text-slate-500 absolute left-4 top-3.5 transition-colors group-focus-within:text-indigo-500" />
              </div>
              <Button
                type="button"
                variant="secondary"
                onClick={handleSelectFolder}
                disabled={!!downloadTask && downloadTask.status === "downloading"}
                className="h-12 px-6 rounded-2xl bg-white/60 hover:bg-white/90 text-slate-700 border border-white/50 shadow-sm backdrop-blur-md transition-all hover:shadow-md active:scale-95"
              >
                浏览
              </Button>
            </div>
          </div>

          {/* 操作按钮区 */}
          {!downloadTask || downloadTask.status === "completed" || downloadTask.status === "failed" ? (
            <Button
              onClick={handleDownload}
              disabled={!url || !savePath || !apiReady}
              className="w-full h-14 text-lg font-semibold rounded-2xl bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 text-white shadow-lg shadow-indigo-500/30 transition-all hover:scale-[1.02] hover:shadow-indigo-500/40 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none border-0"
            >
              <Download className="mr-2.5 h-6 w-6" />
              开始下载
            </Button>
          ) : null}

          {/* 任务重置按钮 */}
           {(downloadTask?.status === "completed" || downloadTask?.status === "failed") && (
             <Button onClick={handleReset} variant="outline" className="w-full h-12 rounded-2xl border-dashed border-2 border-indigo-200 bg-transparent hover:bg-indigo-50/50 text-indigo-600 transition-all hover:border-indigo-300">
               开始新的下载任务
             </Button>
           )}

          {/* 进度条状态 */}
          {downloadTask && downloadTask.status === "downloading" && (
            <div className="bg-white/50 rounded-2xl p-5 space-y-4 border border-white/60 shadow-sm backdrop-blur-sm">
              <div className="flex justify-between text-sm">
                <div className="flex items-center gap-2.5">
                  <div className="p-1.5 bg-indigo-100 rounded-full animate-pulse">
                    <Loader2 className="h-4 w-4 animate-spin text-indigo-600" />
                  </div>
                  <span className="font-semibold text-slate-700">{downloadTask.message}</span>
                </div>
                <span className="text-slate-500 font-medium flex items-center gap-3">
                  {downloadTask.speed && (
                    <span className="text-indigo-600/80 font-mono bg-indigo-50 px-2 py-0.5 rounded text-xs">
                      {downloadTask.speed}
                    </span>
                  )}
                  {downloadTask.eta && (
                    <span className="text-slate-400 text-xs">
                      剩余: {downloadTask.eta}
                    </span>
                  )}
                </span>
              </div>
              <div className="space-y-1.5">
                 <Progress value={Math.min(downloadTask.progress || 0, 99)} className="h-2.5 rounded-full bg-slate-200/50" />
                 <div className="text-right">
                   <span className="text-xs font-semibold text-indigo-600 bg-indigo-50/50 px-2 py-0.5 rounded-full">
                     {(downloadTask.progress || 0).toFixed(1)}%
                   </span>
                 </div>
              </div>
            </div>
          )}

          {/* 成功提示 */}
          {downloadTask && downloadTask.status === "completed" && (
            <div className="bg-green-50/60 border border-green-200/60 rounded-2xl p-5 backdrop-blur-sm shadow-sm">
              <div className="flex gap-4">
                <div className="mt-0.5 bg-green-100 p-2 rounded-full h-fit shadow-sm">
                    <CheckCircle2 className="h-6 w-6 text-green-600" />
                </div>
                <div className="flex-1 space-y-1.5">
                  <h4 className="text-base font-bold text-green-800">
                    下载完成
                  </h4>
                  {downloadTask.title && (
                    <p className="text-sm text-green-700 font-medium line-clamp-1">
                      {downloadTask.title}
                    </p>
                  )}
                  {downloadTask.filePath && (
                    <p className="text-xs text-green-600/90 font-mono break-all bg-green-100/50 p-2 rounded-lg inline-block">
                      {downloadTask.filePath}
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* 失败提示 */}
          {downloadTask && downloadTask.status === "failed" && (
            <div className="bg-red-50/60 border border-red-200/60 rounded-2xl p-5 backdrop-blur-sm shadow-sm">
              <div className="flex gap-4">
                <div className="mt-0.5 bg-red-100 p-2 rounded-full h-fit shadow-sm">
                    <XCircle className="h-6 w-6 text-red-600" />
                </div>
                <div className="flex-1">
                  <h4 className="text-base font-bold text-red-800">
                    下载遇到问题
                  </h4>
                  <p className="text-sm text-red-600 font-medium mt-1">
                    {downloadTask.message}
                  </p>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 底部功能特性 */}
      <div className="relative z-10 mt-12 grid grid-cols-3 gap-6 max-w-2xl w-full text-center px-4">
        <div className="p-4 rounded-2xl bg-white/20 border border-white/30 backdrop-blur-sm hover:bg-white/30 transition-all duration-300 cursor-default group">
          <div className="mx-auto w-12 h-12 rounded-2xl bg-white/50 flex items-center justify-center text-blue-600 shadow-sm mb-3 group-hover:scale-110 transition-transform">
            <Youtube className="w-6 h-6" />
          </div>
          <h3 className="text-base font-semibold text-slate-800 mb-1">多平台支持</h3>
          <p className="text-xs text-slate-600">支持 YouTube 等主流平台</p>
        </div>
        <div className="p-4 rounded-2xl bg-white/20 border border-white/30 backdrop-blur-sm hover:bg-white/30 transition-all duration-300 cursor-default group">
          <div className="mx-auto w-12 h-12 rounded-2xl bg-white/50 flex items-center justify-center text-purple-600 shadow-sm mb-3 group-hover:scale-110 transition-transform">
            <FileVideo className="w-6 h-6" />
          </div>
          <h3 className="text-base font-semibold text-slate-800 mb-1">高清画质</h3>
          <p className="text-xs text-slate-600">自动选择最佳分辨率</p>
        </div>
        <div className="p-4 rounded-2xl bg-white/20 border border-white/30 backdrop-blur-sm hover:bg-white/30 transition-all duration-300 cursor-default group">
          <div className="mx-auto w-12 h-12 rounded-2xl bg-white/50 flex items-center justify-center text-emerald-600 shadow-sm mb-3 group-hover:scale-110 transition-transform">
            <ArrowRight className="w-6 h-6" />
          </div>
          <h3 className="text-base font-semibold text-slate-800 mb-1">快速便捷</h3>
          <p className="text-xs text-slate-600">简洁界面，一键下载</p>
        </div>
      </div>
    </div>
  );
}
