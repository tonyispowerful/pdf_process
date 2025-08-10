import jieba
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from gensim.models import Word2Vec
from difflib import SequenceMatcher
import Levenshtein
from sentence_transformers import SentenceTransformer
import torch
import os
import warnings

# 禁用特定警告
warnings.filterwarnings("ignore", category=UserWarning, module="huggingface_hub")
warnings.filterwarnings("ignore", category=FutureWarning, module="torch")

# 设置环境变量禁用symlinks警告
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'


def tfidf_similarity(text1, text2):
    """使用TF-IDF向量计算余弦相似度"""
    # 中文分词
    words1 = ' '.join(jieba.cut(text1))
    words2 = ' '.join(jieba.cut(text2))
    
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([words1, words2])
    similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    return similarity

def word2vec_similarity(text1, text2):
    """使用Word2Vec计算语义相似度"""
    sentences1 = [list(jieba.cut(text1))]
    sentences2 = [list(jieba.cut(text2))]
    
    # 训练或加载预训练模型
    model = Word2Vec(sentences1 + sentences2, vector_size=100, window=5, min_count=1)
    
    # 计算句子向量并比较相似度
    def get_sentence_vector(sentence, model):
        vectors = [model.wv[word] for word in sentence if word in model.wv]
        if vectors:
            return np.mean(vectors, axis=0)
        return np.zeros(model.vector_size)
    
    vec1 = get_sentence_vector(sentences1[0], model)
    vec2 = get_sentence_vector(sentences2[0], model)
    
    return cosine_similarity([vec1], [vec2])[0][0]
  
def levenshtein_similarity(text1, text2):
    """计算编辑距离相似度"""
    distance = Levenshtein.distance(text1, text2)
    max_len = max(len(text1), len(text2))
    return 1 - distance / max_len if max_len > 0 else 1

def sequence_similarity(text1, text2):
    """使用SequenceMatcher计算相似度"""
    return SequenceMatcher(None, text1, text2).ratio()

def jaro_winkler_similarity(text1, text2):
    """Jaro-Winkler相似度"""
    return Levenshtein.jaro_winkler(text1, text2)
  
def ngram_similarity(text1, text2, n=3):
    """N-gram相似度检测"""
    def get_ngrams(text, n):
        return set([text[i:i+n] for i in range(len(text)-n+1)])
    
    ngrams1 = get_ngrams(text1, n)
    ngrams2 = get_ngrams(text2, n)
    
    intersection = len(ngrams1.intersection(ngrams2))
    union = len(ngrams1.union(ngrams2))
    
    return intersection / union if union > 0 else 0

def shingling_similarity(text1, text2, k=5):
    """Shingling算法"""
    def get_shingles(text, k):
        return set([text[i:i+k] for i in range(len(text)-k+1)])
    
    shingles1 = get_shingles(text1, k)
    shingles2 = get_shingles(text2, k)
    
    jaccard = len(shingles1.intersection(shingles2)) / len(shingles1.union(shingles2))
    return jaccard
  
  
  
  # 使用BERT等预训练模型

def bert_similarity(text1, text2):
    """使用BERT计算语义相似度"""
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    
    embeddings = model.encode([text1, text2])
    similarity = torch.nn.functional.cosine_similarity(
        torch.tensor(embeddings[0]).unsqueeze(0),
        torch.tensor(embeddings[1]).unsqueeze(0)
    )
    return similarity.item()
  
def structure_similarity(text1, text2):
    """基于文档结构的相似度"""
    import re
    
    # 提取结构特征
    def extract_structure(text):
        features = {
            'paragraphs': len(text.split('\n\n')),
            'sentences': len(re.split(r'[。！？]', text)),
            'numbers': len(re.findall(r'\d+', text)),
            'punctuation': len(re.findall(r'[，。；：！？]', text))
        }
        return features
    
    struct1 = extract_structure(text1)
    struct2 = extract_structure(text2)
    
    # 计算结构相似度
    similarities = []
    for key in struct1:
        if struct1[key] + struct2[key] > 0:
            sim = 1 - abs(struct1[key] - struct2[key]) / (struct1[key] + struct2[key])
            similarities.append(sim)
    
    return np.mean(similarities) if similarities else 0
  
  
from db_manager import get_unique_data, get_tender_files


class AdvancedSimilarityDetector:
    def __init__(self):
        self.methods = {
            'tfidf': tfidf_similarity,
            'word2vec': word2vec_similarity,       
            'levenshtein': levenshtein_similarity,
            'sequence': sequence_similarity,      
            'jaro_winkler': jaro_winkler_similarity, 
            'ngram': ngram_similarity,
            'shingling': shingling_similarity,    
            'bert': bert_similarity,
            'structure': structure_similarity
        }
      
        self.weights = {
            'tfidf': 0.20,
            'word2vec': 0.15,
            'levenshtein': 0.10,
            'sequence': 0.05,
            'jaro_winkler': 0.05,
            'ngram': 0.15,
            'shingling': 0.10,
            'bert': 0.15,
            'structure': 0.05
        }
    
    def _get_current_time(self):
      """获取当前时间"""
      from datetime import datetime
      return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  
    def comprehensive_similarity(self, text1, text2, methods=['tfidf', 'word2vec','levenshtein', 'sequence', 'jaro_winkler', 'ngram', 'shingling', 'bert', 'structure']):
        """综合多种方法计算相似度"""
        scores = {}
        for method in methods:
            if method in self.methods:
                try:
                    scores[method] = self.methods[method](text1, text2)
                except Exception as e:
                    print(f"方法 {method} 计算失败: {e}")
                    scores[method] = 0
        
        # 加权平均
        weighted_score = sum(scores[method] * self.weights.get(method, 0.2) 
                           for method in scores)
        
        return {
            'overall_similarity': weighted_score,
            'detailed_scores': scores,
            'is_similar': weighted_score > 0.7  # 阈值可调
        }

    def detect_all_documents(self, threshold=0.5, methods=['tfidf', 'word2vec','levenshtein', 'sequence', 'jaro_winkler', 'ngram', 'shingling', 'bert', 'structure']):
        """检测数据库中所有文档的相似度"""
        all_data = get_unique_data()
        print(f"共有{len(all_data)}个文件")
        if len(all_data) < 2:
            return {"message": "数据库中文档数量不足，无法进行相似度检测"}
        
        # 提取文本内容
        documents = []
        doc_info = []
        for doc in all_data:
            if '原始文本' in doc and doc['原始文本']:
                documents.append(doc['原始文本'])
                doc_info.append({
                    'file_name': doc.get('文件名', 'unknown'),
                    'file_type': doc.get('文件类型', 'unknown'),
                })
        
        # 批量检测相似度
        results = []
        for i in range(len(documents)):
            for j in range(i+1, len(documents)):
                similarity_result = self.comprehensive_similarity(
                    documents[i], documents[j], methods
                )
                print(f"Comparing {doc_info[i]['file_name']} with {doc_info[j]['file_name']} similarity: {similarity_result['overall_similarity']:.4f}")
                
                if similarity_result['overall_similarity'] > threshold:
                    results.append({
                        'doc1': doc_info[i],
                        'doc2': doc_info[j],
                        'similarity_score': similarity_result['overall_similarity'],
                        'detailed_scores': similarity_result['detailed_scores'],
                        'is_highly_similar': similarity_result['overall_similarity'] > 0.8
                    })
        
        # 按相似度排序
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        return results
    
    def detect_bidding_documents(self, threshold=0.7):
        """检测投标文件间的相似度"""
        tender_files = get_tender_files()
        if len(tender_files) < 2:
            return {"message": "投标文件数量不足"}
        
        results = []
        for i in range(len(tender_files)):
            for j in range(i+1, len(tender_files)):
                doc1 = tender_files[i]
                doc2 = tender_files[j]

                if doc1.get('原始文本') and doc2.get('原始文本'):
                    similarity = self.comprehensive_similarity(
                        doc1['原始文本'], doc2['原始文本']
                    )
                    
                    if similarity['overall_similarity'] > threshold:
                        results.append({
                            'company1': doc1.get('投标单位', 'unknown'),
                            'company2': doc2.get('投标单位', 'unknown'),
                            'file1': doc1.get('文件名'),
                            'file2': doc2.get('文件名'),
                            'similarity_score': similarity['overall_similarity'],
                            'plagiarism_risk': 'HIGH' if similarity['overall_similarity'] > 0.8 else 'MEDIUM'
                        })
        
        return sorted(results, key=lambda x: x['similarity_score'], reverse=True)
    
    def compare_with_template(self, target_file_name, template_file_name, methods=['tfidf', 'bert']):
        """将指定文档与模板文档进行比较"""
        from db_manager import get_data_by_file_name
        
        target_doc = get_data_by_file_name(target_file_name)
        template_doc = get_data_by_file_name(template_file_name)
        
        if not target_doc or not template_doc:
            return {"error": "文档未找到"}
        
        if not target_doc.get('content') or not template_doc.get('content'):
            return {"error": "文档内容为空"}
        
        similarity = self.comprehensive_similarity(
            target_doc['content'], 
            template_doc['content'], 
            methods
        )
        
        return {
            'target_file': target_file_name,
            'template_file': template_file_name,
            'similarity_result': similarity,
            'recommendation': self._get_similarity_recommendation(similarity['overall_similarity'])
        }
    
    def find_similar_to_document(self, file_name, threshold=0.5, top_n=5):
        """找到与指定文档最相似的其他文档"""
        from db_manager import get_data_by_file_name
        
        target_doc = get_data_by_file_name(file_name)
        if not target_doc or not target_doc.get('content'):
            return {"error": "目标文档未找到或内容为空"}
        
        all_data = get_all_data()
        similarities = []
        
        for doc in all_data:
            if (doc.get('文件名') != file_name and 
                doc.get('content')):
                
                similarity = self.comprehensive_similarity(
                    target_doc['content'], 
                    doc['content']
                )
                
                if similarity['overall_similarity'] > threshold:
                    similarities.append({
                        'file_name': doc.get('文件名'),
                        'file_type': doc.get('文件类型'),
                        'company': doc.get('采购人名称', doc.get('投标单位')),
                        'similarity_score': similarity['overall_similarity']
                    })
        
        # 返回最相似的前N个文档
        similarities.sort(key=lambda x: x['similarity_score'], reverse=True)
        return similarities[:top_n]
    
    def generate_similarity_report(self, output_file='similarity_report.txt'):
      """生成完整的相似度检测报告"""
      report = []
      report.append("=" * 80)
      report.append("文档相似度检测报告")
      report.append("=" * 80)
      report.append("")
      
      # 投标抄袭检测
      plagiarism = self.detect_bidding_documents(threshold=0.7)

      if isinstance(plagiarism, dict) and 'message' in plagiarism:
          report.append(f"1. 投标抄袭检测 (阈值: 0.7)")
          report.append(f"   {plagiarism['message']}")
          plagiarism_count = 0
      elif isinstance(plagiarism, list):
          plagiarism_count = len(plagiarism)
          report.append(f"1. 投标抄袭检测 (阈值: 0.7)")
          report.append(f"   发现 {plagiarism_count} 对可能抄袭的投标文件")
      else:
          plagiarism_count = 0
          report.append(f"1. 投标抄袭检测 (阈值: 0.7)")
          report.append(f"   检测结果异常")
      
      report.append("")
      
      # 投标抄袭详细结果
      if isinstance(plagiarism, list) and len(plagiarism) > 0:
          report.append("2. 投标抄袭详细结果:")
          for i, result in enumerate(plagiarism, 1):
              try:
                  company1 = result.get('company1', '未知公司1')
                  company2 = result.get('company2', '未知公司2')
                  file1 = result.get('file1', '未知文件1')
                  file2 = result.get('file2', '未知文件2')
                  score = result.get('similarity_score', 0)
                  risk = result.get('plagiarism_risk', 'UNKNOWN')
                  
                  report.append(f"   {'-' * 60}")
                  report.append(f"   抄袭风险检测 #{i}")
                  report.append(f"   {'-' * 60}")
                  report.append(f"   公司1: {company1}")
                  report.append(f"   文件1: {file1}")
                  report.append(f"   公司2: {company2}")
                  report.append(f"   文件2: {file2}")
                  report.append(f"   相似度: {score:.4f}")
                  
                  # 风险等级评估
                  if score > 0.9:
                      risk_level = "极高风险 - 可能存在直接复制"
                  elif score > 0.8:
                      risk_level = "高风险 - 需要进一步审查"
                  elif score > 0.7:
                      risk_level = "中等风险 - 可能存在参考借鉴"
                  elif score > 0.5:
                      risk_level = "低风险 - 属于正常范围"
                  else:
                      risk_level = "极低风险 - 内容差异较大"
                  
                  report.append(f"   风险等级: {risk}")
                  report.append(f"   风险评估: {risk_level}")
                  report.append("")
                  
              except Exception as e:
                  report.append(f"   抄袭检测 #{i}: 数据解析错误 - {str(e)}")
                  report.append("")
      else:
          report.append("2. 投标抄袭详细结果:")
          if isinstance(plagiarism, dict) and 'message' in plagiarism:
              report.append(f"   {plagiarism['message']}")
          else:
              report.append("   未发现投标抄袭风险")
          report.append("")

      # 统计摘要
      report.append("=" * 80)
      report.append("检测统计摘要")
      report.append("=" * 80)
      report.append(f"投标抄袭风险案例: {plagiarism_count}")

      if isinstance(plagiarism, list) and len(plagiarism) > 0:
          high_risk_count = sum(1 for r in plagiarism if r.get('similarity_score', 0) > 0.8)
          medium_risk_count = sum(1 for r in plagiarism if 0.7 <= r.get('similarity_score', 0) <= 0.8)
          low_risk_count = sum(1 for r in plagiarism if r.get('similarity_score', 0) < 0.7)
          
          report.append(f"高风险案例 (>0.8): {high_risk_count}")
          report.append(f"中风险案例 (0.7-0.8): {medium_risk_count}")
          report.append(f"低风险案例 (<0.7): {low_risk_count}")

      report.append("")
      report.append(f"报告生成时间: {self._get_current_time()}")
      report.append("=" * 80)

      # 保存报告
      try:
          with open(output_file, 'w', encoding='utf-8') as f:
              f.write('\n'.join(report))
          print(f"✓ 详细报告已保存到: {output_file}")
          print(f"  包含 {plagiarism_count} 个抄袭风险案例")
      except Exception as e:
          print(f"⚠ 报告保存失败: {e}")

      return {
          'report_file': output_file,
          'plagiarism_cases': plagiarism_count,
          'report_content': '\n'.join(report),
          'plagiarism_results': plagiarism if isinstance(plagiarism, list) else []
      }

    def _get_similarity_recommendation(self, score):
        """根据相似度分数给出建议"""
        if score > 0.9:
            return "极高相似度，可能存在直接复制"
        elif score > 0.8:
            return "高相似度，需要进一步审查"
        elif score > 0.7:
            return "中等相似度，可能存在参考借鉴"
        elif score > 0.5:
            return "低相似度，属于正常范围"
        else:
            return "相似度很低，内容差异较大"
    
    def _analyze_similarity_pattern(self, similarity_result):
        """分析相似度模式"""
        scores = similarity_result['detailed_scores']
        patterns = []
        
        if scores.get('tfidf', 0) > 0.8:
            patterns.append("词汇高度重复")
        if scores.get('structure', 0) > 0.8:
            patterns.append("结构高度相似")
        if scores.get('bert', 0) > 0.8:
            patterns.append("语义高度相似")
        
        return patterns if patterns else ["一般相似"]

  
def create_similarity_detect_report():
    """创建相似度检测报告"""
  
    # 创建检测器实例
    detector = AdvancedSimilarityDetector()
    
    # 直接生成投标文档抄袭检测报告
    print("   开始生成投标抄袭检测报告...")
    report = detector.generate_similarity_report()
    
    return report

create_similarity_detect_report()