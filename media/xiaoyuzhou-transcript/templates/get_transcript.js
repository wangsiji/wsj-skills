const { XiaoyuzhoufmClient } = require('mcp-xiaoyuzhoufm');
const fs = require('fs');

async function getTranscript() {
  const xiaoyu = new XiaoyuzhoufmClient();
  
  // ===== 填你要提取的播客链接 =====
  const episodeUrl = 'https://www.xiaoyuzhoufm.com/episode/{EPISODE_ID}';
  
  try {
    const episodeId = await xiaoyu.extractEpisodeId(episodeUrl);
    console.log('单集ID：', episodeId);

    const episodeInfo = await xiaoyu.getEpisodeInfo(episodeId);
    
    if (!episodeInfo.success) {
      console.log('获取失败');
      return;
    }

    const ep = episodeInfo.episode;
    console.log('标题：', ep.title);
    
    // 判断是否有文字稿
    if (!ep.transcript || ep.transcript.length === 0) {
      console.log('该节目未生成文字稿');
      // 备选：输出 show notes
      if (ep.shownotes) {
        console.log('\nShow Notes 时间戳：');
        console.log(ep.shownotes);
      }
      return;
    }

    // 输出带时间戳的文字稿
    console.log('\n===== 文字稿内容 =====\n');
    const lines = ep.transcript.map(item => {
      const m = Math.floor(item.start / 60);
      const s = Math.floor(item.start % 60);
      return `[${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}] ${item.content}`;
    });
    
    console.log(lines.join('\n'));
    
    // 保存到文件
    fs.writeFileSync('transcript.txt', lines.join('\n'), 'utf-8');
    console.log('\n文字稿已保存到 transcript.txt');

  } catch (err) {
    console.error('获取失败：', err.message);
  }
}

getTranscript();
