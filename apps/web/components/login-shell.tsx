"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import {
  Building2,
  CheckCircle2,
  KeyRound,
  LockKeyhole,
  Mail,
  ShieldCheck,
  Store,
  UserRound
} from "lucide-react";

type Audience = "用户" | "商家" | "管理员";
type AuthMode = "login" | "register" | "forgot";
type AccountType = "customer" | "merchant" | "admin";
type AdminRole =
  | "admin_operator"
  | "admin_customer_service"
  | "admin_customer_service_lead"
  | "admin_risk"
  | "admin_finance"
  | "admin_tech"
  | "audit_readonly";

type UserPublic = {
  id: string;
  email: string;
  display_name: string;
  account_type: AccountType;
  roles: string[];
  permissions: string[];
};

type TokenResponse = {
  access_token: string;
  user: UserPublic;
};

type RegistrationResponse = {
  user: UserPublic;
  console: "customer" | "merchant" | "admin";
  next_step: string;
  merchant_ids?: string[];
};

type PasswordResetRequestResponse = {
  message: string;
  reset_token?: string | null;
};

type LoginShellProps = {
  audience: Audience;
  mode?: AuthMode;
  eyebrow: string;
  title: string;
  description: string;
  accentClassName: string;
  accountType: AccountType;
  primaryHref: string;
  registerHref?: string;
  forgotHref: string;
  loginHref: string;
};

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

const audienceIcon = {
  用户: UserRound,
  商家: Store,
  管理员: ShieldCheck
};

const modeCopy = {
  login: {
    title: "登录",
    subtitle: "使用邮箱和密码进入对应账号空间",
    button: "登录",
    helper: "登录会校验账号类型，普通用户、商家和管理员不能跨端进入其他工作台。"
  },
  register: {
    title: "注册",
    subtitle: "创建新账号并进入对应端侧",
    button: "创建账号",
    helper: "用户自助注册，商家创建店主账号，管理员需要平台邀请码并只能选择受限角色。"
  },
  forgot: {
    title: "找回密码",
    subtitle: "发送一次性重置凭证并按账号类型校验",
    button: "发送重置链接",
    helper: "若账号存在，将发送重置说明；页面不会暴露账号是否存在。"
  }
};

const adminRoleOptions: { label: string; value: AdminRole }[] = [
  { label: "平台客服", value: "admin_customer_service" },
  { label: "平台运营", value: "admin_operator" },
  { label: "客服主管", value: "admin_customer_service_lead" },
  { label: "风控审核", value: "admin_risk" },
  { label: "财务管理员", value: "admin_finance" },
  { label: "技术管理员", value: "admin_tech" },
  { label: "只读审计", value: "audit_readonly" }
];

async function postAuth<T>(path: string, body: Record<string, unknown>): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  const payload = (await response.json().catch(() => null)) as unknown;

  if (!response.ok) {
    throw new Error(readApiError(payload, response.status));
  }

  return payload as T;
}

function readApiError(payload: unknown, status: number): string {
  if (payload && typeof payload === "object" && "detail" in payload) {
    const detail = (payload as { detail: unknown }).detail;
    if (typeof detail === "string") {
      return detail;
    }
    if (Array.isArray(detail)) {
      return detail
        .map((item) => {
          if (item && typeof item === "object" && "msg" in item) {
            return String((item as { msg: unknown }).msg);
          }
          return String(item);
        })
        .join("；");
    }
  }
  return `请求失败，状态码 ${status}`;
}

function readFormValue(formData: FormData, name: string): string {
  return String(formData.get(name) ?? "").trim();
}

function storageKey(accountType: AccountType): string {
  return `commerce.auth.${accountType}`;
}

export function LoginShell({
  audience,
  mode = "login",
  eyebrow,
  title,
  description,
  accentClassName,
  accountType,
  primaryHref,
  registerHref,
  forgotHref,
  loginHref
}: LoginShellProps) {
  const Icon = audienceIcon[audience];
  const copy = modeCopy[mode];
  const isRegister = mode === "register";
  const isForgot = mode === "forgot";
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [resetRequested, setResetRequested] = useState(false);
  const [resetToken, setResetToken] = useState("");
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const primaryButtonText =
    isForgot && resetRequested ? "确认重置密码" : isSubmitting ? "处理中..." : copy.button;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);
    setStatusMessage(null);
    setIsSubmitting(true);

    const formData = new FormData(event.currentTarget);
    const email = readFormValue(formData, "email");
    const password = readFormValue(formData, "password");
    const displayName = readFormValue(formData, "display_name");

    try {
      if (mode === "login") {
        await handleLogin(email, password);
      } else if (mode === "register") {
        await handleRegister(formData, email, password, displayName);
      } else if (resetRequested) {
        await handlePasswordResetConfirm(formData, email);
      } else {
        await handlePasswordResetRequest(email);
      }
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "请求失败，请稍后重试");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleLogin(email: string, password: string) {
    const response = await postAuth<TokenResponse>("/auth/login", {
      email,
      password,
      account_type: accountType
    });
    window.localStorage.setItem(
      storageKey(accountType),
      JSON.stringify({
        accessToken: response.access_token,
        accountType,
        user: response.user
      })
    );
    setStatusMessage(`${response.user.display_name} 已登录，正在进入${audience}工作区。`);
    window.location.assign(primaryHref);
  }

  async function handleRegister(
    formData: FormData,
    email: string,
    password: string,
    displayName: string
  ) {
    const body: Record<string, unknown> = {
      email,
      password,
      display_name: displayName
    };
    if (accountType === "merchant") {
      body.shop_name = readFormValue(formData, "shop_name");
    }
    if (accountType === "admin") {
      body.invite_code = readFormValue(formData, "invite_code");
      body.role = readFormValue(formData, "role");
    }

    const response = await postAuth<RegistrationResponse>(
      `/auth/register/${accountType}`,
      body
    );
    const merchantHint =
      response.merchant_ids && response.merchant_ids.length > 0
        ? `，商家范围 ${response.merchant_ids[0]}`
        : "";
    setStatusMessage(
      `${response.user.display_name} 的${audience}账号已创建${merchantHint}。请返回登录。`
    );
  }

  async function handlePasswordResetRequest(email: string) {
    const response = await postAuth<PasswordResetRequestResponse>("/auth/password/forgot", {
      email,
      account_type: accountType
    });
    setResetRequested(true);
    setResetToken(response.reset_token ?? "");
    setStatusMessage(
      response.reset_token
        ? "本地环境已生成重置凭证，可直接确认新密码。"
        : response.message
    );
  }

  async function handlePasswordResetConfirm(formData: FormData, email: string) {
    await postAuth("/auth/password/reset", {
      email,
      account_type: accountType,
      reset_token: readFormValue(formData, "reset_token"),
      new_password: readFormValue(formData, "new_password")
    });
    setResetRequested(false);
    setResetToken("");
    setStatusMessage("密码已重置，请返回登录并使用新密码。");
  }

  return (
    <main className="min-h-screen bg-[#f4f5f7] px-4 py-6 text-commerce-ink md:px-6">
      <section className="mx-auto grid min-h-[calc(100vh-3rem)] max-w-7xl gap-6 lg:grid-cols-[1fr_440px] lg:items-center">
        <div className="rounded-md bg-white p-6 md:p-10">
          <p className="text-sm font-bold uppercase tracking-[0.08em] text-slate-500">
            {eyebrow}
          </p>
          <h1 className="mt-4 max-w-2xl text-4xl font-black tracking-normal">{title}</h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-slate-600">{description}</p>
          <div className="mt-8 grid gap-3 md:grid-cols-3">
            {["账号类型隔离", "权限校验", "审计留痕"].map((item) => (
              <div className="rounded-md bg-slate-50 p-4" key={item}>
                <CheckCircle2 className="h-5 w-5 text-commerce-red" aria-hidden="true" />
                <p className="mt-3 text-sm font-bold">{item}</p>
                <p className="mt-1 text-xs leading-5 text-slate-500">
                  按 {accountType} 身份进入对应端侧
                </p>
              </div>
            ))}
          </div>
        </div>

        <form
          className="rounded-md border border-slate-200 bg-white p-6 shadow-sm"
          onSubmit={handleSubmit}
        >
          <div className={`mb-5 h-1.5 w-16 rounded-full ${accentClassName}`} />
          <div className="flex items-center gap-3">
            <span className="flex h-11 w-11 items-center justify-center rounded-md bg-slate-100 text-commerce-red">
              <Icon className="h-5 w-5" aria-hidden="true" />
            </span>
            <div>
              <h2 className="text-2xl font-black">
                {audience}
                {copy.title}
              </h2>
              <p className="mt-1 text-sm text-slate-500">{copy.subtitle}</p>
            </div>
          </div>

          <div className="mt-6 grid gap-4">
            <label className="grid gap-2 text-sm font-bold text-slate-700">
              邮箱
              <span className="relative">
                <Mail
                  className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
                  aria-hidden="true"
                />
                <input
                  className="h-12 w-full rounded-md border border-slate-300 pl-10 pr-3 text-base outline-none transition focus:border-commerce-teal focus:ring-2 focus:ring-commerce-teal/20"
                  name="email"
                  type="email"
                  autoComplete="email"
                  placeholder={`${accountType}@example.com`}
                  required
                />
              </span>
            </label>

            {!isForgot ? (
              <label className="grid gap-2 text-sm font-bold text-slate-700">
                密码
                <span className="relative">
                  <LockKeyhole
                    className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
                    aria-hidden="true"
                  />
                  <input
                    className="h-12 w-full rounded-md border border-slate-300 pl-10 pr-3 text-base outline-none transition focus:border-commerce-teal focus:ring-2 focus:ring-commerce-teal/20"
                    name="password"
                    type="password"
                    autoComplete={isRegister ? "new-password" : "current-password"}
                    placeholder={isRegister ? "至少 12 位密码" : "请输入密码"}
                    required
                    minLength={isRegister ? 12 : 1}
                  />
                </span>
              </label>
            ) : null}

            {isRegister ? (
              <>
                <label className="grid gap-2 text-sm font-bold text-slate-700">
                  昵称/联系人
                  <input
                    className="h-12 rounded-md border border-slate-300 px-3 text-base outline-none transition focus:border-commerce-teal focus:ring-2 focus:ring-commerce-teal/20"
                    name="display_name"
                    placeholder="请输入名称"
                    required
                  />
                </label>
                {accountType === "merchant" ? (
                  <label className="grid gap-2 text-sm font-bold text-slate-700">
                    店铺名称
                    <span className="relative">
                      <Building2
                        className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
                        aria-hidden="true"
                      />
                      <input
                        className="h-12 w-full rounded-md border border-slate-300 pl-10 pr-3 text-base outline-none transition focus:border-commerce-teal focus:ring-2 focus:ring-commerce-teal/20"
                        name="shop_name"
                        placeholder="例如 Northstar 演示店"
                        required
                      />
                    </span>
                  </label>
                ) : null}
                {accountType === "admin" ? (
                  <>
                    <label className="grid gap-2 text-sm font-bold text-slate-700">
                      平台邀请码
                      <span className="relative">
                        <KeyRound
                          className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
                          aria-hidden="true"
                        />
                        <input
                          className="h-12 w-full rounded-md border border-slate-300 pl-10 pr-3 text-base outline-none transition focus:border-commerce-teal focus:ring-2 focus:ring-commerce-teal/20"
                          name="invite_code"
                          placeholder="由平台管理员发放"
                          required
                          minLength={8}
                        />
                      </span>
                    </label>
                    <label className="grid gap-2 text-sm font-bold text-slate-700">
                      管理员角色
                      <select
                        className="h-12 rounded-md border border-slate-300 px-3 text-base outline-none transition focus:border-commerce-teal focus:ring-2 focus:ring-commerce-teal/20"
                        name="role"
                        defaultValue="admin_customer_service"
                      >
                        {adminRoleOptions.map((role) => (
                          <option key={role.value} value={role.value}>
                            {role.label}
                          </option>
                        ))}
                      </select>
                    </label>
                  </>
                ) : null}
              </>
            ) : null}

            {isForgot && resetRequested ? (
              <>
                <label className="grid gap-2 text-sm font-bold text-slate-700">
                  重置凭证
                  <input
                    className="h-12 rounded-md border border-slate-300 px-3 text-base outline-none transition focus:border-commerce-teal focus:ring-2 focus:ring-commerce-teal/20"
                    name="reset_token"
                    value={resetToken}
                    onChange={(event) => setResetToken(event.target.value)}
                    placeholder="从邮件或本地响应中复制"
                    required
                    minLength={32}
                  />
                </label>
                <label className="grid gap-2 text-sm font-bold text-slate-700">
                  新密码
                  <span className="relative">
                    <LockKeyhole
                      className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
                      aria-hidden="true"
                    />
                    <input
                      className="h-12 w-full rounded-md border border-slate-300 pl-10 pr-3 text-base outline-none transition focus:border-commerce-teal focus:ring-2 focus:ring-commerce-teal/20"
                      name="new_password"
                      type="password"
                      autoComplete="new-password"
                      placeholder="至少 12 位新密码"
                      required
                      minLength={12}
                    />
                  </span>
                </label>
              </>
            ) : null}

            <div className="rounded-md bg-slate-50 p-3 text-xs leading-5 text-slate-600">
              {copy.helper}
            </div>

            {statusMessage ? (
              <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm leading-6 text-emerald-800">
                {statusMessage}
              </div>
            ) : null}
            {errorMessage ? (
              <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm leading-6 text-red-700">
                {errorMessage}
              </div>
            ) : null}

            <button
              className="h-12 rounded-md bg-commerce-ink px-4 text-sm font-bold text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:bg-slate-400"
              type="submit"
              disabled={isSubmitting}
            >
              {primaryButtonText}
            </button>
          </div>

          <div className="mt-6 grid gap-3 border-t border-slate-100 pt-5 text-sm">
            {mode !== "login" ? (
              <Link className="font-bold text-commerce-red" href={loginHref}>
                已有账号，返回登录
              </Link>
            ) : (
              <Link className="font-bold text-commerce-red" href={forgotHref}>
                找回密码
              </Link>
            )}
            {registerHref && mode !== "register" ? (
              <Link className="font-bold text-commerce-teal" href={registerHref}>
                创建{audience}账号
              </Link>
            ) : null}
          </div>
        </form>
      </section>
    </main>
  );
}
