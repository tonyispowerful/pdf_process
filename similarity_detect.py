import jieba
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from gensim.models import Word2Vec
from difflib import SequenceMatcher
import Levenshtein
from sentence_transformers import SentenceTransformer
import torch

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
  
  
  
  
from db_manager import get_all_data, get_bidding_files, get_tender_files, get_data_by_company


class AdvancedSimilarityDetector:
    def __init__(self):
        self.methods = {
            'tfidf': tfidf_similarity,
            'levenshtein': levenshtein_similarity,
            'ngram': ngram_similarity,
            'structure': structure_similarity,
            'bert': bert_similarity
        }
        self.weights = {
            'tfidf': 0.3,
            'levenshtein': 0.2,
            'ngram': 0.2,
            'structure': 0.1,
            'bert': 0.2
        }
    
    def comprehensive_similarity(self, text1, text2, methods=['tfidf', 'levenshtein', 'ngram']):
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

    def detect_similar_documents(self, threshold=0.7, methods=['tfidf', 'levenshtein', 'ngram']):
        """检测数据库中所有文档的相似度"""
        all_data = get_all_data()
        if len(all_data) < 2:
            return {"message": "数据库中文档数量不足，无法进行相似度检测"}
        
        # 提取文本内容
        documents = []
        doc_info = []
        for doc in all_data:
            if 'text' in doc and doc['text']:
                documents.append(doc['text'])
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
    
    def detect_bidding_plagiarism(self, threshold=0.7):
        """检测投标文件间的抄袭"""
        tender_files = get_tender_files()
        if len(tender_files) < 2:
            return {"message": "投标文件数量不足"}
        
        results = []
        for i in range(len(tender_files)):
            for j in range(i+1, len(tender_files)):
                doc1 = tender_files[i]
                doc2 = tender_files[j]
                
                if doc1.get('content') and doc2.get('content'):
                    similarity = self.comprehensive_similarity(
                        doc1['content'], doc2['content']
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
    
    def company_similarity_analysis(self, company_name, threshold=0.6):
        """分析某公司文档的内部相似度"""
        company_docs = get_data_by_company(company_name)
        
        if len(company_docs) < 2:
            return {"message": f"公司 {company_name} 的文档数量不足"}
        
        results = []
        for i in range(len(company_docs)):
            for j in range(i+1, len(company_docs)):
                doc1, doc2 = company_docs[i], company_docs[j]
                
                if doc1.get('content') and doc2.get('content'):
                    similarity = self.comprehensive_similarity(
                        doc1['content'], doc2['content']
                    )
                    
                    if similarity['overall_similarity'] > threshold:
                        results.append({
                            'file1': doc1.get('文件名'),
                            'file2': doc2.get('文件名'),
                            'similarity_score': similarity['overall_similarity'],
                            'analysis': self._analyze_similarity_pattern(similarity)
                        })
        
        return {
            'company': company_name,
            'total_documents': len(company_docs),
            'similar_pairs': len(results),
            'similarity_details': results
        }
    
    def generate_similarity_report(self, output_file='similarity_report.txt'):
        """生成完整的相似度检测报告"""
        report = []
        report.append("=" * 50)
        report.append("文档相似度检测报告")
        report.append("=" * 50)
        report.append("")
        
        # 总体相似度检测
        all_similar = self.detect_similar_documents(threshold=0.6)
        report.append(f"1. 总体相似度检测 (阈值: 0.6)")
        report.append(f"   发现 {len(all_similar)} 对相似文档")
        report.append("")
        
        # 投标抄袭检测
        plagiarism = self.detect_bidding_plagiarism(threshold=0.7)
        report.append(f"2. 投标抄袭检测 (阈值: 0.7)")
        report.append(f"   发现 {len(plagiarism)} 对可能抄袭的投标文件")
        report.append("")
        
        # 详细结果
        report.append("3. 详细相似度结果:")
        if isinstance(all_similar, list) and len(all_similar) > 0:
            for i, result in enumerate(all_similar[:3], 1):  # 只显示前3个
                doc1_name = result.get('doc1', {}).get('file_name', '未知文档')
                doc2_name = result.get('doc2', {}).get('file_name', '未知文档')
                score = result.get('similarity_score', 0)
                
                report.append(f"   {i}. {doc1_name} <-> {doc2_name}")
                report.append(f"      相似度: {score:.3f}")
                report.append("")
        elif isinstance(all_similar, dict) and 'message' in all_similar:
            report.append(f"   {all_similar['message']}")
            report.append("")
        else:
            report.append("   暂无相似文档发现")
            report.append("")
        
        #保存报告
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))
        
        return {
            'report_file': output_file,
            'total_similar_pairs': len(all_similar),
            'plagiarism_cases': len(plagiarism)
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


# 便捷函数
def quick_similarity_check(threshold=0.7):
    """快速相似度检查"""
    detector = AdvancedSimilarityDetector()
    return detector.detect_similar_documents(threshold)

def check_plagiarism():
    """快速抄袭检查"""
    detector = AdvancedSimilarityDetector()
    return detector.detect_bidding_plagiarism()
  
  
# 创建检测器实例
detector = AdvancedSimilarityDetector()

# 检测所有文档相似度
results = detector.detect_similar_documents(threshold=0.7)

# 检测投标抄袭
plagiarism = detector.detect_bidding_plagiarism()

# 生成报告
report = detector.generate_similarity_report()