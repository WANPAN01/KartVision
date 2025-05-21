from typing import List, Tuple, Dict, Any, Optional
import re


class User:
    """ユーザー（プレイヤー）を表すクラス"""
    
    def __init__(self, raw_name: str):
        """
        ユーザーの初期化
        
        Args:
            raw_name (str): OCRで認識されたプレイヤー名
        """
        self.raw_name = raw_name
        self.name: Optional[str] = None  # タグを除いた名前（オプション）
        self.points: List[int] = []      # レースごとの獲得ポイント
        
    def add_point(self, point: int):
        """
        ポイントを追加する
        
        Args:
            point (int): 追加するポイント
        """
        self.points.append(point)
        
    def sum_points(self) -> int:
        """
        合計ポイントを計算する
        
        Returns:
            int: 合計ポイント
        """
        return sum(self.points)
        
    def set_name(self, name: str):
        """
        タグを除いた名前を設定する
        
        Args:
            name (str): 設定する名前
        """
        self.name = name
        
    def __str__(self) -> str:
        """
        ユーザー情報の文字列表現
        
        Returns:
            str: ユーザー情報
        """
        return f"{self.raw_name}: points={self.points}"


class Team:
    """チームを表すクラス"""
    
    def __init__(self, users: List[User], tag: str):
        """
        チームの初期化
        
        Args:
            users (List[User]): チームに所属するユーザーのリスト
            tag (str): チームを識別するタグ
        """
        self.users = users
        self.tag = tag
        
    def sum_points_dict(self) -> Dict[str, Any]:
        """
        チームの合計ポイント情報を辞書形式で取得
        
        Returns:
            Dict[str, Any]: タグと合計ポイントを含む辞書
        """
        return {
            "tag": self.tag,
            "sum_points": sum(user.sum_points() for user in self.users),
            "users": [user.raw_name for user in self.users],  # ユーザー名を追加
            "user_count": len(self.users)                     # ユーザー数を追加
        }
        
    def __str__(self) -> str:
        """
        チーム情報の文字列表現
        
        Returns:
            str: チーム情報
        """
        return f"Team {self.tag}: " + ", ".join(str(u) for u in self.users)


def create_teams_with_tags(
    ranking: List[Tuple[str, int]],
    group_num: int = 2,
    tag_positions: List[str] = ["prefix", "suffix"],
) -> List[Team]:
    """
    プレイヤー名からタグでチーム分けを行う
    
    Args:
        ranking (List[Tuple[str, int]]): (プレイヤー名, ポイント)のリスト
        group_num (int, optional): チームあたりのプレイヤー数
        tag_positions (List[str], optional): タグの位置（"prefix"/"suffix"）
        
    Returns:
        List[Team]: 作成されたチームのリスト
    """
    # ユーザーの作成
    all_users = []
    for raw_name, point in ranking:
        user = User(raw_name)
        user.add_point(point)
        all_users.append(user)
    
    final_teams: List[Team] = []
    remaining_users = all_users[:]
    
    # タグ長を長い順に試す（最大10文字から1文字まで）
    for tag_len in range(10, 0, -1):
        # 指定された位置（プレフィックス/サフィックス）でのチーム分けを試みる
        for position in tag_positions:
            grouping_map = {}
            
            # 各ユーザーからタグ候補を抽出
            for user in remaining_users:
                rn = user.raw_name
                if len(rn) < tag_len:
                    continue
                    
                # タグ候補と残りの部分を抽出
                if position == "prefix":
                    # 前方タグ
                    candidate = rn[:tag_len].strip()
                    rest = rn[tag_len:].strip()
                elif position == "suffix":
                    # 後方タグ
                    suffix_candidate = rn[-tag_len:]
                    rest = rn[:-tag_len].rstrip()
                    
                    # 特殊な後方タグ "/s" の処理
                    if suffix_candidate.endswith("/s"):
                        candidate = "/s"
                        rest = rn[:-2].rstrip()
                    else:
                        # 先頭の余分な文字を削除
                        candidate = re.sub(r"^[_\s]+", "", suffix_candidate)
                        candidate = candidate.strip()
                else:
                    continue
                    
                # 空のタグはスキップ
                if not candidate:
                    continue
                    
                # タグごとにユーザーをグループ化
                if candidate not in grouping_map:
                    grouping_map[candidate] = []
                grouping_map[candidate].append((user, rest))
            
            # 十分なユーザー数を持つタグでチームを作成
            to_remove = []
            for tag_candidate, user_info_list in grouping_map.items():
                if len(user_info_list) >= group_num:
                    team_users = []
                    for u, name_remaining in user_info_list:
                        u.set_name(name_remaining)
                        team_users.append(u)
                        to_remove.append(u)
                        
                    new_team = Team(team_users, tag_candidate)
                    final_teams.append(new_team)
            
            # チーム化したユーザーを残りリストから削除
            remaining_users = [u for u in remaining_users if u not in to_remove]
            
            # すべてユーザーをチーム化できたら終了
            if not remaining_users:
                break
                
        # すべてユーザーをチーム化できたら終了
        if not remaining_users:
            break
    
    # チーム化できなかったユーザーはそれぞれ個別チームとして扱う
    while remaining_users:
        user = remaining_users.pop()
        # 名前の最初の単語をタグとして使用
        fallback_tag = user.raw_name.split()[0] if user.raw_name else "?"
        new_team = Team([user], fallback_tag)
        final_teams.append(new_team)
        
    return final_teams
