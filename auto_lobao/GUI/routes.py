from Router import Router, DataStrategyEnum
from index_view import IndexView
from profile_view import ProfileView
from settings_view import SettingsView
from data_view import DataView
from receita_contratada import receita_contratada_view
from tendencia import tendencias
from de_para_canais import de_para_canais

router = Router(DataStrategyEnum.QUERY)

router.routes = {
  "/": IndexView,
  "/profile": ProfileView,
  "/settings": SettingsView,
  "/data": DataView,
  "/tendencias": tendencias,
  "/receitacontratada" :receita_contratada_view,
  "/deparacanais": de_para_canais,
}