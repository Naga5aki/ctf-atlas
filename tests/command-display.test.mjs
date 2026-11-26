import assert from 'node:assert/strict';
import test from 'node:test';
import { isStandaloneCommand, isRepeatedSummary, commandCaption, normalizeCommandText } from '../src/lib/command-display.mjs';

test('recognizes standalone command paragraphs in legacy tool guides', () => {
  assert.equal(isStandaloneCommand('binwalk sample.bin'), true);
  assert.equal(isStandaloneCommand('strings -a sample.bin | grep flag'), true);
  assert.equal(isStandaloneCommand('python3 inspect.py sample.bin'), true);
  assert.equal(isStandaloneCommand('montage *.png -tile 10x10 -geometry +0+0 result.png'), true);
  assert.equal(isStandaloneCommand('stegsnow -S carrier.txt'), true);
  assert.equal(isStandaloneCommand('npiet -cs 5 challenge.png'), true);
});

test('leaves explanatory prose and mixed command descriptions as text', () => {
  assert.equal(isStandaloneCommand('Steghide 对 PNG 格式支持极弱'), false);
  assert.equal(isStandaloneCommand('file filename识别文件类型'), false);
  assert.equal(isStandaloneCommand('#-e=extract，提取所有文件'), false);
  assert.equal(isStandaloneCommand('输出会显示偏移、类型和大小'), false);
});

test('only removes a tool lead when it repeats the visible summary exactly', () => {
  assert.equal(isRepeatedSummary('分析嵌入数据。', '分析嵌入数据。'), true);
  assert.equal(isRepeatedSummary('分析嵌入数据。', '分析嵌入数据，并说明偏移。'), false);
});

test('turns shorthand command comments into readable captions', () => {
  assert.equal(commandCaption('#扫描并列出文件结构'), '扫描并列出文件结构');
  assert.equal(commandCaption('#-e=extract，提取文件'), '-e=extract，提取文件');
  assert.equal(commandCaption('# ImageMagick 7 (Windows)'), 'ImageMagick 7 (Windows)');
  assert.equal(commandCaption('# Disk DescriptorFile'), null);
  assert.equal(commandCaption('普通说明文字'), null);
});

test('normalizes a known case sensitive command name for copying', () => {
  assert.equal(normalizeCommandText('Binwalk -e sample.bin'), 'binwalk -e sample.bin');
  assert.equal(normalizeCommandText('strings sample.bin'), 'strings sample.bin');
});
