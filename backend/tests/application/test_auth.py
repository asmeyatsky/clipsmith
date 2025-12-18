import pytest
from backend.application.use_cases.register_user import RegisterUserUseCase
from backend.application.use_cases.authenticate_user import AuthenticateUserUseCase
from backend.application.dtos.auth_dto import RegisterRequestDTO, LoginRequestDTO
from backend.domain.entities.user import User


class TestRegisterUserUseCase:
    def test_register_user_success(self, user_repo):
        use_case = RegisterUserUseCase(user_repo)
        
        dto = RegisterRequestDTO(
            username="testuser",
            email="test@example.com",
            password="securepassword123"
        )
        
        result = use_case.execute(dto)
        
        assert result.username == "testuser"
        assert result.email == "test@example.com"
        assert result.is_active is True

    def test_register_user_duplicate_email(self, user_repo):
        use_case = RegisterUserUseCase(user_repo)
        
        dto = RegisterRequestDTO(
            username="user1",
            email="duplicate@example.com",
            password="password123"
        )
        use_case.execute(dto)
        
        # Try to register with same email
        dto2 = RegisterRequestDTO(
            username="user2",
            email="duplicate@example.com",
            password="password456"
        )
        
        with pytest.raises(ValueError):
            use_case.execute(dto2)


class TestAuthenticateUserUseCase:
    def test_login_success(self, user_repo):
        # First register a user
        register_use_case = RegisterUserUseCase(user_repo)
        register_dto = RegisterRequestDTO(
            username="loginuser",
            email="login@example.com",
            password="mypassword123"
        )
        register_use_case.execute(register_dto)
        
        # Now try to login
        auth_use_case = AuthenticateUserUseCase(user_repo)
        login_dto = LoginRequestDTO(
            email="login@example.com",
            password="mypassword123"
        )
        
        result = auth_use_case.execute(login_dto)
        
        assert result is not None
        assert result.access_token is not None
        assert result.token_type == "bearer"
        assert result.user.email == "login@example.com"
        assert result.user.username == "loginuser"

    def test_login_wrong_password(self, user_repo):
        # First register a user
        register_use_case = RegisterUserUseCase(user_repo)
        register_dto = RegisterRequestDTO(
            username="wrongpassuser",
            email="wrongpass@example.com",
            password="correctpassword"
        )
        register_use_case.execute(register_dto)
        
        # Try to login with wrong password
        auth_use_case = AuthenticateUserUseCase(user_repo)
        login_dto = LoginRequestDTO(
            email="wrongpass@example.com",
            password="wrongpassword"
        )
        
        result = auth_use_case.execute(login_dto)
        assert result is None

    def test_login_nonexistent_user(self, user_repo):
        auth_use_case = AuthenticateUserUseCase(user_repo)
        login_dto = LoginRequestDTO(
            email="nonexistent@example.com",
            password="anypassword"
        )
        
        result = auth_use_case.execute(login_dto)
        assert result is None
