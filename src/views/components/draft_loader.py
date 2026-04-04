"""Draft loading helper functions for RGB asset detail."""
from __future__ import annotations

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QGridLayout

from src.data.repository.setting_repository import SettingRepository
from src.data.service.wallet_data_service import WalletDataService
from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletSignatureType
from src.model.enums.enums_model import WalletType
from src.model.rgb_model import RgbAssetPageLoadModel
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.viewmodels.main_view_model import MainViewModel
from src.views.components.transaction_detail_frame import TransactionDetailFrame


def load_transfer_draft(
    asset_id: str,
    row_index: int,
    scroll_area_widget_contents,
    scroll_area_widget_layout: QGridLayout,
    view_model: MainViewModel,
) -> int:
    """Load transfer draft and add to scroll area.

    Args:
        asset_id: The asset ID.
        row_index: Current row index in scroll area.
        scroll_area_widget_contents: The scroll area widget contents.
        scroll_area_widget_layout: The scroll area layout.
        view_model: The main view model.

    Returns:
        Updated row index after adding draft frame.
    """
    try:
        if SettingRepository.get_wallet_type() != WalletType.OFFLINE_TYPE_WALLET:
            svc = WalletDataService.get_session()
            if svc is not None:
                transfer_draft = svc.get_draft_transfer(str(asset_id))
                if transfer_draft:
                    draft_frame = TransactionDetailFrame(
                        scroll_area_widget_contents,
                    )
                    draft_frame.transaction_date.setText(
                        QCoreApplication.translate(
                            IRIS_WALLET_TRANSLATIONS_CONTEXT, 'resume_transfer', None,
                        ),
                    )
                    draft_frame.transaction_time.setText(
                        QCoreApplication.translate(
                            IRIS_WALLET_TRANSLATIONS_CONTEXT, 'draft', None,
                        ),
                    )
                    draft_amt = transfer_draft.get('amount')
                    draft_frame.transaction_amount.setText(
                        str(draft_amt) if draft_amt else '',
                    )
                    draft_frame.transaction_amount.setStyleSheet(
                        'font: 15px "Inter"; color: #D0D3DD; background: transparent; border: none; font-weight: 600;',
                    )
                    draft_frame.transaction_type.hide()
                    draft_frame.transfer_type.hide()
                    draft_frame.setCursor(
                        QCursor(Qt.CursorShape.PointingHandCursor),
                    )

                    def on_resume_transfer(_p=None, _data=transfer_draft):
                        view_model.page_navigation.send_cfa_page(
                            draft_data=_data,
                        )

                    draft_frame.click_frame.connect(on_resume_transfer)
                    scroll_area_widget_layout.addWidget(
                        draft_frame, row_index, 0, 1, 1,
                    )
                    return row_index + 1
    except Exception as e:
        print(f"Error loading transfer draft: {e}")  # noqa: T201
    return row_index


def load_secondary_issuance_drafts(
    asset_id: str,
    image_path: str,
    row_index: int,
    scroll_area_widget_contents,
    scroll_area_widget_layout: QGridLayout,
    view_model: MainViewModel,
) -> int:
    """Load secondary issuance drafts for IFA assets.

    Args:
        asset_id: The asset ID.
        image_path: Path to asset image.
        row_index: Current row index in scroll area.
        scroll_area_widget_contents: The scroll area widget contents.
        scroll_area_widget_layout: The scroll area layout.
        view_model: The main view model.

    Returns:
        Updated row index after adding draft frames.
    """
    try:
        access_type = SettingRepository.get_wallet_access_type()
        is_multisig = SettingRepository.get_wallet_signature_type(
        ) == WalletSignatureType.MULTI_SIG_WALLET
        if access_type == WalletAccessType.WATCH_ONLY or is_multisig and SettingRepository.get_wallet_type() != WalletType.OFFLINE_TYPE_WALLET:
            svc = WalletDataService.get_session()
            if svc is not None:
                drafts = svc.list_ifa_secondary_drafts(
                    asset_id=str(asset_id),
                ) or []
                for d in drafts:
                    amt = d.get('amount')
                    draft_id = d.get('id')
                    d_asset_name = d.get('asset_name')
                    draft_frame = TransactionDetailFrame(
                        scroll_area_widget_contents,
                    )
                    draft_frame.transaction_date.setText(
                        QCoreApplication.translate(
                            IRIS_WALLET_TRANSLATIONS_CONTEXT, 'resume_secondary_issuance', None,
                        ),
                    )
                    draft_frame.transaction_time.setText(
                        QCoreApplication.translate(
                            IRIS_WALLET_TRANSLATIONS_CONTEXT, 'draft', None,
                        ),
                    )
                    draft_frame.transaction_amount.setText(
                        str(amt) if amt is not None else '',
                    )
                    draft_frame.transaction_amount.setStyleSheet(
                        'font: 15px "Inter"; color: #D0D3DD; background: transparent; border: none; font-weight: 600;',
                    )
                    draft_frame.transaction_type.hide()
                    draft_frame.transfer_type.hide()
                    draft_frame.setCursor(
                        QCursor(Qt.CursorShape.PointingHandCursor),
                    )

                    def on_resume_click(_p=None, _asset_id=str(asset_id), _draft_id=draft_id, _asset_name=d_asset_name):
                        try:
                            svc_inner = WalletDataService.get_session()
                            if svc_inner is not None and _draft_id is not None:
                                svc_inner.set_active_secondary_draft(
                                    int(_draft_id), str(_asset_id),
                                )
                        except Exception:
                            pass
                        params = RgbAssetPageLoadModel(
                            asset_id=str(_asset_id),
                            asset_name=_asset_name,
                            image_path=image_path,
                            asset_type='IFA',
                            is_secondary_issuance=True,
                        )
                        view_model.page_navigation.issue_ifa_secondary_page(
                            params, draft_id=int(
                                _draft_id,
                            ) if _draft_id is not None else None, from_draft=True,
                        )
                    draft_frame.click_frame.connect(on_resume_click)
                    scroll_area_widget_layout.addWidget(
                        draft_frame, row_index, 0, 1, 1,
                    )
                    row_index += 1
    except Exception:
        pass
    return row_index
