"""
任务类型定义模块
定义禅道任务类型枚举和映射字典
"""

from enum import Enum


class TaskType(Enum):
    """任务类型枚举"""
    # 需求相关
    REQUIREMENT_DOCKING = "requirementDocking"  # 需求
    MARKET_USER_RESEARCH = "marketUserResearch"  # 市场/用户调研
    REQUIREMENT_ANALYSIS = "requirementAnalysis"  # 需求分析
    COMMON_REQUIREMENT = "commonRequirement"  # 通用需求

    # 设计相关
    PRODUCT_SOLUTION_DESIGN = "productSolutionDesign"  # 产品方案设计
    PRODUCT_SOLUTION_REVIEW = "productSolutionReview"  # 产品方案评审
    UI_DESIGN = "uiDesign"  # UI设计
    TECHNICAL_PRE_RESEARCH = "technicalPreResearch"  # 技术预研
    REQUIREMENT_UI_REVIEW = "requirementUiReview"  # 需求/UI评审
    ARCHITECTURE_DESIGN = "architectureDesign"  # 架构设计
    OUTLINE_DESIGN = "outlineDesign"  # 概要设计
    DETAILED_DESIGN = "detailedDesign"  # 详细设计

    # 开发相关
    COMMON_DEVELOP = "commonDevelop"  # 通用研发
    FRONTEND_CODING = "frontendCoding"  # 前端编码
    BACKEND_CODING = "backendCoding"  # 后端编码
    JOINT_DEBUGGING = "jointDebugging"  # 联调
    CODE_REVIEW = "codeReview"  # 代码走查
    SELF_TESTING_UNIT_TESTING = "selfTestingUnitTesting"  # 自测/单元测试
    RD_ACHIEVEMENT_DEMO = "rdAchievementDemo"  # 研发成果演示

    # 测试相关
    SMOKE_TEST_CASES = "smokeTestCases"  # 冒烟用例
    TEST_CASES = "testCases"  # 测试用例
    RD_DESIGN_REVIEW = "rdDesignReview"  # 研发设计评审
    UI_REVIEW = "uiReview"  # UI走查
    PRODUCT_ACCEPTANCE = "productAcceptance"  # 产品验收
    VERSION_TEST_SUBMISSION = "versionTestSubmission"  # 版本提测
    TEST_CASE_REVIEW = "testCaseReview"  # 测试用例评审
    COMMON_TEST = "commonTest"  # 通用测试
    TEST_ACCESS_CHECK = "testAccessCheck"  # 测试准入检查
    PRODUCT_FUNCTION_TESTING = "productFunctionTesting"  # 产品功能测试
    REGRESSION_TESTING = "regressionTesting"  # 回归测试
    INTEGRATION_TESTING = "integrationTesting"  # 集成测试
    AUTOMATED_TESTING = "automatedTesting"  # 自动化测试
    SECURITY_TESTING = "securityTesting"  # 安全测试
    PERFORMANCE_TESTING = "performanceTesting"  # 性能测试
    TEST_REPORT = "testReport"  # 测试报告

    # 生产支持
    PRODUCTION_ISSUE_REPRODUCTION = "productionIssueReproduction"  # 生产问题复现
    PROJECT_UPGRADE_SUPPORT = "projectUpgradeSupport"  # 项目升级支持
    PRODUCTION_ISSUE_HANDLING = "productionIssueHandling"  # 生产问题处理
    PRODUCTION_ISSUE_REVIEW = "productionIssueReview"  # 生产问题复盘

    # 研发项目管理
    RD_PROJECT_INITIATION = "rdProjectInitiation"  # 研发项目立项
    RD_PROJECT_MANAGEMENT = "rdProjectManagement"  # 研发项目管理
    RD_PROJECT_CLOSURE_REVIEW = "rdProjectClosureReview"  # 研发项目结项复盘

    # 质量管理
    QUALITY_SYSTEM_CONSTRUCTION = "qualitySystemConstruction"  # 质量体系建设
    QUALITY_AUDIT_INSPECTION = "qualityAuditInspection"  # 质量审计稽查
    QUALITY_QUALITY_METRICS = "qualityQualityMetrics"  # 质量统计度量
    QUALITY_ISSUE_RECTIFICATION = "qualityIssueRectification"  # 质量问题整改

    # 项目支持
    COMMON_SUPPORT = "commonSupport"  # 通用支持
    PRE_SALES_SUPPORT = "preSalesSupport"  # 售前支持
    PROJECT_TESTING_DEMO_SUPPORT = "projectTestingDemoSupport"  # 项目测试与演示支持
    PROJECT_DOCUMENT_WRITING = "projectDocumentWriting"  # 项目文档编写
    PRODUCTION_SECURITY_REINFORCEMENT = "productionSecurityReinforcement"  # 生产安全加固
    PRODUCTION_PERFORMANCE_OPTIMIZATION = "productionPerformanceOptimization"  # 生产性能优化
    PROJECT_OTHER_SUPPORT = "projectOtherSupport"  # 项目其他支持

    # 运营相关
    TRAINING = "training"  # 培训
    LEAVE_APPLICATION = "leaveApplication"  # 请假
    OTHER = "other"  # 其他
    CONTENT_OPERATION = "contentOperation"  # 内容运营
    DATA_AUDIT = "dataAudit"  # 数据审核
    COMMON_OPERATION = "commonOperation"  # 通用运营
    CUSTOM_SERVICE = "customService"  # 客服


# 任务类型映射字典（中文 -> 英文）
task_type_dict = {
    "需求": "requirementDocking",
    "市场/用户调研": "marketUserResearch",
    "产品方案设计": "productSolutionDesign",
    "产品方案评审": "productSolutionReview",
    "研发项目立项": "rdProjectInitiation",
    "研发项目管理": "rdProjectManagement",
    "需求分析": "requirementAnalysis",
    "通用需求": "commonRequirement",
    "UI设计": "uiDesign",
    "技术预研": "technicalPreResearch",
    "需求/UI评审": "requirementUiReview",
    "架构设计": "architectureDesign",
    "概要设计": "outlineDesign",
    "通用研发": "commonDevelop",
    "详细设计": "detailedDesign",
    "冒烟用例": "smokeTestCases",
    "测试用例": "testCases",
    "研发设计评审": "rdDesignReview",
    "前端编码": "frontendCoding",
    "后端编码": "backendCoding",
    "联调": "jointDebugging",
    "代码走查": "codeReview",
    "自测/单元测试": "selfTestingUnitTesting",
    "研发成果演示": "rdAchievementDemo",
    "UI走查": "uiReview",
    "产品验收": "productAcceptance",
    "版本提测": "versionTestSubmission",
    "测试用例评审": "testCaseReview",
    "通用测试": "commonTest",
    "测试准入检查": "testAccessCheck",
    "产品功能测试": "productFunctionTesting",
    "回归测试": "regressionTesting",
    "集成测试": "integrationTesting",
    "自动化测试": "automatedTesting",
    "安全测试": "securityTesting",
    "性能测试": "performanceTesting",
    "测试报告": "testReport",
    "生产问题复现": "productionIssueReproduction",
    "项目升级支持": "projectUpgradeSupport",
    "生产问题处理": "productionIssueHandling",
    "生产问题复盘": "productionIssueReview",
    "研发项目结项复盘": "rdProjectClosureReview",
    "质量体系建设": "qualitySystemConstruction",
    "质量审计稽查": "qualityAuditInspection",
    "质量统计度量": "qualityQualityMetrics",
    "质量问题整改": "qualityIssueRectification",
    "通用支持": "commonSupport",
    "售前支持": "preSalesSupport",
    "项目测试与演示支持": "projectTestingDemoSupport",
    "项目文档编写": "projectDocumentWriting",
    "生产安全加固": "productionSecurityReinforcement",
    "生产性能优化": "productionPerformanceOptimization",
    "项目其他支持": "projectOtherSupport",
    "培训": "training",
    "请假": "leaveApplication",
    "其他": "other",
    "内容运营": "contentOperation",
    "数据审核": "dataAudit",
    "通用运营": "commonOperation",
    "客服": "customService"
}
