from difflib import SequenceMatcher
from flask import Flask
from user import User, Team
from typing import List, Tuple, Optional, Dict, Any


def similarity_ratio(s1: str, s2: str) -> float:
    """
    2つの文字列の類似度を計算する
    
    Args:
        s1 (str): 比較する文字列1
        s2 (str): 比較する文字列2
        
    Returns:
        float: 類似度（0.0～1.0）
    """
    return SequenceMatcher(None, s1, s2).ratio()


def find_similar_user(users: List[User], new_raw_name: str, threshold: float = 0.6) -> Optional[User]:
    """
    新しいプレイヤー名に最も類似したユーザーを見つける
    
    Args:
        users (List[User]): 既存ユーザーのリスト
        new_raw_name (str): 新しいプレイヤー名
        threshold (float): 類似と判定する閾値
        
    Returns:
        Optional[User]: 類似したユーザー（閾値以上の類似度がない場合はNone）
    """
    best_user = None
    best_score = 0.0
    
    for user in users:
        score = similarity_ratio(user.raw_name, new_raw_name)
        if score > best_score:
            best_score = score
            best_user = user
            
    if best_score >= threshold:
        return best_user
    return None


def find_team_by_first_letter(teams: List[Team], first_letter: str) -> Optional[Team]:
    """
    タグ（先頭文字）からチームを見つける
    
    Args:
        teams (List[Team]): チームのリスト
        first_letter (str): 検索するタグ
        
    Returns:
        Optional[Team]: 見つかったチーム（見つからない場合はNone）
    """
    for team in teams:
        if team.tag == first_letter:
            return team
    return None


class KartFlask(Flask):
    """
    カスタムFlaskアプリケーションクラス
    チーム管理と結果集計機能を持つ
    """
    
    def __init__(self, *args, **kwargs):
        """初期化"""
        super(KartFlask, self).__init__(*args, **kwargs)
        self.teams: List[Team] = []
        
    def set_teams(self, teams: List[Team]):
        """
        チームリストを設定する
        
        Args:
            teams (List[Team]): 設定するチームのリスト
        """
        self.teams = teams
        
    def update(self, ranking: List[Tuple[str, int]]):
        """
        新しいレース結果でチーム/ユーザー情報を更新する
        
        Args:
            ranking (List[Tuple[str, int]]): (プレイヤー名, ポイント)のリスト
        """
        # すべてのユーザーのフラットリスト
        all_users = [user for team in self.teams for user in team.users]
        
        for raw_name, point in ranking:
            # 完全一致するユーザーを探す
            matched_user = None
            for user in all_users:
                if user.raw_name == raw_name:
                    matched_user = user
                    break
                    
            # 完全一致がなければ類似マッチを試みる
            if matched_user is None:
                matched_user = find_similar_user(all_users, raw_name, threshold=0.6)
                
            # それでも見つからなければ新規ユーザー＋チーム作成
            if matched_user is None:
                new_user = User(raw_name)
                new_user.add_point(point)
                all_users.append(new_user)
                
                # タグ（先頭文字）からチームを探す
                first_letter = raw_name[0] if raw_name else "?"
                existing_team = find_team_by_first_letter(self.teams, first_letter)
                
                if existing_team:
                    existing_team.users.append(new_user)
                else:
                    new_team = Team([new_user], first_letter)
                    self.teams.append(new_team)
            else:
                # 既存ユーザーにポイント追加
                matched_user.add_point(point)
                
    def high_score_list(self) -> List[Dict[str, Any]]:
        """
        チームごとの合計点リストを取得する
        
        Returns:
            List[Dict[str, Any]]: タグと合計ポイントを含む辞書のリスト
        """
        score_dicts = [team.sum_points_dict() for team in self.teams]
        score_dicts.sort(key=lambda x: x["sum_points"], reverse=True)
        return score_dicts