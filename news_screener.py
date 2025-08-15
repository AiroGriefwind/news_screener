import os
import json
import time
import re
from pathlib import Path
from typing import Dict, List, Optional
from openai import OpenAI
from docx import Document
import argparse
from datetime import datetime

class NewsClassifier:
    def __init__(self, api_key: str, rate_limit_delay: float = 2.0):
        """Initialize the News Classifier for Kimi AI"""
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.moonshot.cn/v1"
        )
        self.rate_limit_delay = rate_limit_delay
        print("Kimi AI client initialized successfully")

    def is_new_metadata_format(self, text: str) -> bool:
        """Check if the text is a metadata line (has at least two '|' separators)"""
        if not text:
            return False
        return text.count('|') >= 2

    def extract_articles_from_docx(self, file_path: str) -> List[Dict[str, str]]:
        """
        Extract articles from DOCX using metadata-based detection.
        Logic: 
        - Metadata lines have >= 2 '|' characters
        - Line before metadata = title (start of article)
        - Content continues until line before next title
        """
        doc = Document(file_path)
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        
        articles = []
        current_article = None
        i = 0
        n = len(paragraphs)

        while i < n:
            line = paragraphs[i]
            
            # Found a metadata line
            if self.is_new_metadata_format(line):
                # The line before metadata is the title
                title_line = paragraphs[i-1] if i >= 1 else ""
                
                # Save previous article if exists
                if current_article:
                    articles.append(current_article)
                
                # Start new article
                current_article = {
                    'title': title_line,
                    'metadata': line,
                    'content': '',
                    'section': self._extract_section_from_metadata(line)
                }
                
                i += 1  # Move past metadata line
                
                # Collect content lines until next article title
                content_lines = []
                while i < n:
                    # Check if next line is metadata (meaning current line is title of next article)
                    if i + 1 < n and self.is_new_metadata_format(paragraphs[i + 1]):
                        break
                    content_lines.append(paragraphs[i])
                    i += 1
                
                current_article['content'] = ' '.join(content_lines).strip()
            else:
                i += 1

        # Don't forget the last article
        if current_article:
            articles.append(current_article)

        return articles

    def _extract_section_from_metadata(self, metadata: str) -> str:
        """Extract section info from metadata line"""
        # Try to extract section from metadata like "香港經濟日報 A09 國際動態 |817 字 |2025-08-15"
        parts = metadata.split('|')[0].strip().split()
        if len(parts) >= 3:
            return parts[-1]  # Last part before first |
        return "Unknown"

    def analyze_article_with_kimi(self, article: Dict[str, str]) -> Dict:
        """Send article to Kimi AI for 5W1H analysis"""
        prompt = f"""
        请分析这篇新闻文章的"硬新闻"特征，基于5W1H标准（谁、什么、何时、何地、为什么、如何）。

        文章标题：{article['title']}
        文章内容：{article['content'][:3000]}

        请评估：
        1. 谁(WHO)：是否清楚识别了关键人物/实体？(评分1-5)
        2. 什么(WHAT)：是否清楚描述了具体事件/行动？(评分1-5)
        3. 何时(WHEN)：是否提供了时间/日期信息？(评分1-5)
        4. 何地(WHERE)：是否明确指定了地点？(评分1-5)
        5. 为什么(WHY)：是否解释了原因/动机？(评分1-5)
        6. 如何(HOW)：是否描述了方法/过程？(评分1-5)

        请以以下JSON格式返回分析结果：
        {{
            "is_hard_news": true/false,
            "overall_score": 0-30,
            "analysis": {{
                "who_score": 1-5,
                "what_score": 1-5,
                "when_score": 1-5,
                "where_score": 1-5,
                "why_score": 1-5,
                "how_score": 1-5
            }},
            "missing_elements": ["缺失的5W1H元素列表"],
            "recommendation": "分类说明的简要解释",
            "first_three_paragraphs_analysis": "分析前三段是否包含5W1H信息"
        }}

        判断"硬新闻"的标准：
        - 总分 ≥ 20（满分30）
        - 至少4个元素得分 ≥ 3
        - 前三段包含关键信息（谁、什么、何时、何地）
        """
        
        try:
            messages = [
                {
                    "role": "system", 
                    "content": "你是Kimi，由Moonshot AI提供的人工智能助手。你擅长中文和英文对话，专业分析新闻内容的5W1H结构。"
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ]
            
            completion = self.client.chat.completions.create(
                model="moonshot-v1-32k",
                messages=messages,
                temperature=0.3
            )
            
            response_text = completion.choices[0].message.content
            
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                analysis = json.loads(json_str)
            else:
                # Fallback if JSON extraction fails
                analysis = {
                    "is_hard_news": False,
                    "overall_score": 0,
                    "analysis": {
                        "who_score": 0,
                        "what_score": 0,
                        "when_score": 0,
                        "where_score": 0,
                        "why_score": 0,
                        "how_score": 0
                    },
                    "missing_elements": ["all"],
                    "recommendation": "API response parsing failed",
                    "first_three_paragraphs_analysis": "Unable to analyze"
                }
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing article '{article['title'][:30]}...': {str(e)}")
            return {
                "is_hard_news": False,
                "overall_score": 0,
                "analysis": {
                    "who_score": 0,
                    "what_score": 0,
                    "when_score": 0,
                    "where_score": 0,
                    "why_score": 0,
                    "how_score": 0
                },
                "missing_elements": ["all"],
                "recommendation": f"Error: {str(e)}",
                "first_three_paragraphs_analysis": "Error occurred"
            }
    
    def process_document(self, input_file_path: str) -> None:
        """Process entire document and save results"""
        print(f"Processing document: {input_file_path}")
        
        # Extract articles using improved metadata-based method
        print("Extracting articles using metadata detection...")
        articles = self.extract_articles_from_docx(input_file_path)
        print(f"Found {len(articles)} articles")
        
        # Display first few articles for verification
        print("\n=== EXTRACTION VERIFICATION ===")
        for i, article in enumerate(articles[:3], 1):
            print(f"\nArticle {i}:")
            print(f"Title: {article['title']}")
            print(f"Metadata: {article['metadata']}")
            print(f"Content preview: {article['content'][:100]}...")
            print(f"Section: {article['section']}")
        
        # Process each article
        results = []
        for i, article in enumerate(articles, 1):
            print(f"Analyzing article {i}/{len(articles)}: {article['title'][:50]}...")
            
            # Analyze with Kimi AI
            analysis = self.analyze_article_with_kimi(article)
            
            # Combine article data with analysis
            result = {
                "article_info": {
                    "title": article["title"],
                    "metadata": article["metadata"],
                    "section": article["section"],
                    "content_length": len(article["content"]),
                    "content_preview": article["content"][:200] + "..." if len(article["content"]) > 200 else article["content"]
                },
                "analysis": analysis,
                "timestamp": datetime.now().isoformat(),
                "article_index": i
            }
            
            results.append(result)
            
            # Rate limiting
            time.sleep(self.rate_limit_delay)
        
        # Save results
        self.save_results(input_file_path, results)
        
        # Print summary
        self.print_summary(results)
    
    def save_results(self, input_file_path: str, results: List[Dict]) -> None:
        """Save analysis results to JSON file"""
        input_path = Path(input_file_path)
        output_file = input_path.parent / f"{input_path.stem}_kimi_analysis.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"Results saved to: {output_file}")
    
    def print_summary(self, results: List[Dict]) -> None:
        """Print analysis summary"""
        total_articles = len(results)
        hard_news_count = sum(1 for r in results if r["analysis"]["is_hard_news"])
        
        print("\n" + "="*50)
        print("KIMI AI 新闻分析总结")
        print("="*50)
        print(f"总分析文章数: {total_articles}")
        print(f"硬新闻文章数: {hard_news_count}")
        print(f"软新闻文章数: {total_articles - hard_news_count}")
        print(f"硬新闻比例: {(hard_news_count/total_articles)*100:.1f}%")
        
        print(f"\n硬新闻文章列表:")
        for result in results:
            if result["analysis"]["is_hard_news"]:
                score = result["analysis"]["overall_score"]
                title = result["article_info"]["title"]
                print(f"  - {title[:60]}... (得分: {score}/30)")


def main():
    parser = argparse.ArgumentParser(description="使用Kimi AI分类新闻文章 - 改进版")
    parser.add_argument("input_file", help="输入.docx文件路径")
    parser.add_argument("--api-key", required=True, help="Kimi AI API密钥")
    parser.add_argument("--delay", type=float, default=2.0, help="API调用间隔（秒）")
    
    args = parser.parse_args()
    
    # Validate input file
    if not os.path.exists(args.input_file):
        print(f"错误: 找不到输入文件 '{args.input_file}'")
        return
    
    if not args.input_file.endswith('.docx'):
        print("错误: 输入文件必须是.docx格式")
        return
    
    # Initialize classifier and process
    classifier = NewsClassifier(args.api_key, args.delay)
    classifier.process_document(args.input_file)


if __name__ == "__main__":
    main()
