from fastapi import APIRouter, HTTPException,status
from typing import List

from api_naturalize.auth.models.user_model import UserModel
from api_naturalize.auth.schemas.user_schemas import UserResponse
from api_naturalize.leader_board.models.leader_board_model import LeaderBoardModel
from api_naturalize.leader_board.schemas.leader_board_schemas import LeaderboardCreate, LeaderboardUpdate, \
    LeaderboardResponse, Leaderboard_Response

router = APIRouter(prefix="/leaderboards", tags=["leaderboards"])

# GET all leader_boards
@router.get("/", response_model=List[LeaderboardResponse],status_code=status.HTTP_200_OK)
async def get_all_leader_boards(skip: int = 0, limit: int = 10):
    
    """
    Get all leader_boards with pagination
    """
    leader_boards = await LeaderBoardModel.find_all().skip(skip).limit(limit).to_list()
    return leader_boards







@router.get("/filter", response_model=List[Leaderboard_Response], status_code=status.HTTP_200_OK)
async def get_all_leader_boards(skip: int = 0, limit: int = 10):

    leader_boards = await LeaderBoardModel.find_all().skip(skip).limit(limit).to_list()

    # সব user_id একসাথে collect
    user_ids = [lb.user_id for lb in leader_boards]

    users = await UserModel.find(
        UserModel.id.in_(user_ids)
    ).to_list()

    user_map = {str(user.id): user for user in users}

    res = []
    for lb in leader_boards:
        data = lb.model_dump()
        user = user_map.get(str(lb.user_id))
        data["user"] = UserResponse.model_validate(user) if user else None
        res.append(Leaderboard_Response(**data))

    return res











# GET leader_board by ID
@router.get("/{id}", response_model=LeaderboardResponse,status_code=status.HTTP_200_OK)
async def get_leader_board(id: str):
    
    """
    Get leader_board by ID
    """
    leader_board = await LeaderBoardModel.get(id)
    if not leader_board:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="LeaderBoard not found")
    return leader_board

# POST create new leader_board
@router.post("/", response_model=LeaderboardResponse,status_code=status.HTTP_201_CREATED)
async def create_leader_board(leader_board_data: LeaderboardCreate):
    
    """
    Create a new leader_board
    """
    leader_board_dict = leader_board_data.model_dump()
    leader_board = LeaderBoardModel(**leader_board_dict)
    await leader_board.create()
    return leader_board

# PATCH update leader_board
@router.patch("/{id}", response_model=LeaderboardResponse,status_code=status.HTTP_200_OK)
async def update_leader_board(id: str, leader_board_data: LeaderboardUpdate):
    
    """
    Update leader_board information
    """
    leader_board = await LeaderBoardModel.get(id)
    if not leader_board:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="LeaderBoard not found")

    update_data = leader_board_data.model_dump(exclude_unset=True)
    await leader_board.update({"$set": update_data})
    return await LeaderBoardModel.get(id)

# DELETE leader_board
@router.delete("/{id}",status_code=status.HTTP_200_OK)
async def delete_leader_board(id: str):
    
    """
    Delete leader_board by ID
    """
    leader_board = await LeaderBoardModel.get(id)
    if not leader_board:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="LeaderBoard not found")

    await leader_board.delete()
    return {"message": "LeaderBoard deleted successfully"}
